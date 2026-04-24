"""
Main FastAPI application for document management service.
Provides REST endpoints for document upload, retrieval, and text extraction.
"""
import logging
import json
import uuid
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import jwt
from jwt import InvalidTokenError
from sqlalchemy.exc import SQLAlchemyError
from services.file_storage import FileStorageError

from config import settings
from models import (
    DocumentResponse,
    ExtractedTextResponse,
    UploadResponse,
    DocumentWithTextResponse,
    SemanticSearchResponse,
    SearchResult,
    AnalyzeRequest,
    AnalyzeCreateResponse,
    AnalyzePropertyRequest,
    AnalyzePropertyCreateResponse,
    AnalysisStatusResponse,
    AnalysisOutputResponse,
)
from services.upload_service import upload_service
from services.database import db_service
from services.vector_service import vector_service
from services.analysis_tasks import run_analysis_task, run_property_analysis_task
from services.dependency_checker import dependency_checker
from services.text_validator import text_validator
from services.authz import ensure_document_access
from services.logging_config import configure_logging, set_log_context, clear_log_context
from routes.report_routes import router as report_router

# ============================================================================
# Logging Configuration
# ============================================================================

configure_logging(log_dir=settings.LOG_DIR, log_level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)
logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)


# ============================================================================
# Request ID Middleware
# ============================================================================

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Inject a unique request_id into every request's log context.

    The ID is taken from the incoming X-Request-ID header (so upstream proxies
    can supply a trace ID) or generated as a UUID4 if absent. It is added to
    every log record emitted during the request via the thread-local context
    filter in logging_config, and echoed back in the X-Request-ID response header
    so clients can correlate their own logs.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        set_log_context(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_log_context("request_id")


# ============================================================================
# FastAPI Application Setup
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_startup_checks()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready document management service for real estate analysis platform",
    lifespan=lifespan,
)

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)


PUBLIC_PATHS = {
    "/health",
    "/openapi.json",
}

PUBLIC_PREFIXES = (
    "/docs",
    "/redoc",
)

PROTECTED_PREFIXES = (
    "/upload",
    "/documents",
    "/search",
    "/analyze",
    "/reports",
    "/system",
)


def _extract_access_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    cookie_name = settings.AUTH_COOKIE_NAME or "taqim_session"
    cookie_token = request.cookies.get(cookie_name)
    if cookie_token:
        return cookie_token

    return None


def _decode_session(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.AUTH_SECRET, algorithms=["HS256"])


def _can_access_document(request: Request, document: Any) -> bool:
    try:
        ensure_document_access(request=request, document=document)
        return True
    except HTTPException:
        return False


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
        return await call_next(request)

    if not settings.AUTH_REQUIRED:
        return await call_next(request)

    if not any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return await call_next(request)

    if not settings.AUTH_SECRET:
        logger.error("AUTH_SECRET must be configured when AUTH_REQUIRED=True")
        return JSONResponse(
            status_code=500,
            content={"error": "Authentication service misconfigured"},
        )

    token = _extract_access_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Authentication required"})

    try:
        session = _decode_session(token)
    except InvalidTokenError:
        return JSONResponse(status_code=401, content={"error": "Invalid authentication token"})
    except (TypeError, ValueError) as e:
        logger.error("Token verification failed: %s", str(e))
        return JSONResponse(status_code=401, content={"error": "Invalid authentication token"})

    role = str(session.get("role", "")).lower()
    if path.startswith("/system") and role != "admin":
        return JSONResponse(status_code=403, content={"error": "Admin role required"})

    request.state.session = session
    return await call_next(request)


# ============================================================================
# Startup and Shutdown Events
# ============================================================================

async def run_startup_checks():
    """Initialize database, check dependencies, and initialize services on startup."""
    try:
        if settings.AUTH_REQUIRED and not settings.AUTH_SECRET:
            raise RuntimeError("AUTH_SECRET is required when AUTH_REQUIRED=True")

        if settings.SKIP_DEPENDENCY_CHECK:
            logger.warning("Skipping dependency checks because SKIP_DEPENDENCY_CHECK=True")
        else:
            # Check system dependencies
            logger.info("Checking system dependencies...")
            all_available, warnings, errors = dependency_checker.check_all()

            # Log dependency status
            if warnings:
                logger.warning("Dependency warnings:")
                for warning in warnings:
                    logger.warning(f"  {warning}")

            if errors:
                logger.error("Critical dependency errors:")
                for error in errors:
                    logger.error(f"  {error}")
                raise RuntimeError("Critical dependencies missing. Cannot start service.")

            # Print detailed dependency report
            dependency_report = dependency_checker.get_status_report()
            logger.info(f"Dependency Report:\n{dependency_report}")

            # Log format support status
            format_support = dependency_checker.get_format_support_status()
            logger.info(f"Document format support: {format_support}")

        # Initialize database
        logger.info("Initializing database...")
        db_service.init_db()
        logger.info("Database initialized successfully")
        
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Failed to initialize service on startup: {str(e)}")
        raise


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status of the service
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.post(
    "/analyze",
    response_model=AnalyzeCreateResponse,
    summary="Queue asynchronous analysis for a document",
    tags=["Analysis"]
)
async def queue_analysis(request: Request, payload: AnalyzeRequest) -> AnalyzeCreateResponse:
    """
    Trigger async document analysis.

    Flow:
    1. Validate document exists
    2. Create analysis row with queued status
    3. Enqueue Celery task
    """
    try:
        document = db_service.get_document(payload.document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {payload.document_id} not found"
            )
        ensure_document_access(request=request, document=document)

        analysis = db_service.create_analysis(
            document_id=payload.document_id,
            model_version=payload.model_version or "v1"
        )
        db_service.add_analysis_event(analysis.id, stage="queued")

        task = run_analysis_task.delay(payload.document_id, analysis.id)

        return AnalyzeCreateResponse(
            success=True,
            analysis_id=analysis.id,
            document_id=payload.document_id,
            status=analysis.status,
            task_id=task.id,
        )
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Failed to queue analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while queuing analysis"
        )


@app.post(
    "/analyze/property",
    response_model=AnalyzePropertyCreateResponse,
    summary="Queue asynchronous analysis for a property dossier",
    tags=["Analysis"]
)
async def queue_property_analysis(request: Request, payload: AnalyzePropertyRequest) -> AnalyzePropertyCreateResponse:
    """
    Trigger async property-level analysis over multiple document IDs.
    """
    try:
        document_ids = list(dict.fromkeys(payload.document_ids or []))
        if not document_ids:
            raise HTTPException(status_code=400, detail="document_ids is required")

        missing_ids = [doc_id for doc_id in document_ids if not db_service.get_document(doc_id)]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Documents not found: {missing_ids}",
            )

        for doc_id in document_ids:
            ensure_document_access(request=request, document=db_service.get_document(doc_id))

        analysis = db_service.create_analysis(
            document_id=document_ids[0],
            model_version="property-v1",
        )
        db_service.add_analysis_event(
            analysis.id,
            stage="queued_property",
            payload={
                "document_ids": document_ids,
                "property_name": payload.property_name,
            },
        )

        run_property_analysis_task.delay(document_ids, analysis.id)

        return AnalyzePropertyCreateResponse(
            success=True,
            analysis_id=analysis.id,
            document_ids=document_ids,
            status=analysis.status,
            report_url=f"/reports/{analysis.id}/html",
        )
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Failed to queue property analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while queuing property analysis",
        )


@app.get(
    "/analyze/{analysis_id}",
    response_model=AnalysisStatusResponse,
    summary="Get analysis status and outputs",
    tags=["Analysis"]
)
async def get_analysis_status(analysis_id: int, request: Request) -> AnalysisStatusResponse:
    """
    Retrieve analysis status and outputs when available.
    """
    try:
        analysis = db_service.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )

        document = db_service.get_document(analysis.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        ensure_document_access(request=request, document=document)

        output = db_service.get_analysis_output(analysis_id)
        response_output = None

        if output:
            response_output = AnalysisOutputResponse(
                legal_json=output.legal_json,
                risk_json=output.risk_json,
                valuation_json=output.valuation_json,
                final_json=output.final_json,
            )

        return AnalysisStatusResponse(
            analysis_id=analysis.id,
            document_id=analysis.document_id,
            status=analysis.status,
            started_at=analysis.started_at,
            finished_at=analysis.finished_at,
            error=analysis.error,
            model_version=analysis.model_version,
            outputs=response_output,
        )
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Failed to fetch analysis status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching analysis status"
        )


# ============================================================================
# Document Upload Endpoint
# ============================================================================

@app.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a document",
    tags=["Documents"]
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    document_type: str = Query(None, description="Optional document type classification"),
    property_id: str = Query(None, description="Optional property ID reference")
) -> UploadResponse:
    """
    Upload a document and extract text content.
    
    Supports formats: PDF, DOCX, PNG, TXT
    
    - **file**: Multipart file upload (required)
    - **document_type**: Optional classification (e.g., "listing", "report")
    - **property_id**: Optional reference to property ID
    
    Returns:
        Upload response with document ID and status
        
    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        logger.info(f"Received upload request for file: {file.filename}")

        # Reject oversized uploads before reading the body into memory.
        # Content-Length is not guaranteed, so we cap the read with a sentinel byte.
        if file.size is not None and file.size > settings.MAX_FILE_SIZE:
            max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size ({max_mb:.0f} MB)",
            )

        # Read file content
        content = await file.read()

        # Secondary size check for clients that don't send Content-Length.
        if len(content) > settings.MAX_FILE_SIZE:
            max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size ({max_mb:.0f} MB)",
            )

        if not content:
            logger.warning("Upload failed: empty file content")
            raise HTTPException(
                status_code=400,
                detail="File content is empty"
            )

        # Process upload through service
        result = upload_service.process_upload(
            filename=file.filename,
            file_content=content,
            document_type=document_type,
            property_id=property_id
        )
        
        if not result['success']:
            logger.warning(f"Upload processing failed: {result['error']}")
            raise HTTPException(
                status_code=400,
                detail=result['error'] or result['message']
            )
        
        logger.info(f"Upload successful: {file.filename} (ID: {result['document_id']})")
        return UploadResponse(
            success=True,
            message=result['message'],
            document_id=result['document_id'],
            filename=result['filename']
        )
        
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, FileStorageError, SQLAlchemyError) as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during file upload"
        )


# ============================================================================
# Document Retrieval Endpoints
# ============================================================================

@app.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata",
    tags=["Documents"]
)
async def get_document(document_id: int, request: Request) -> DocumentResponse:
    """
    Retrieve document metadata by ID.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document metadata
        
    Raises:
        HTTPException: If document not found
    """
    try:
        logger.info(f"Retrieving document: {document_id}")
        document = db_service.get_document(document_id)
        
        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        ensure_document_access(request=request, document=document)
        
        return DocumentResponse.model_validate(document)
        
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving document"
        )


@app.get(
    "/documents/{document_id}/text",
    response_model=ExtractedTextResponse,
    summary="Get extracted text",
    tags=["Documents"]
)
async def get_document_text(document_id: int, request: Request) -> ExtractedTextResponse:
    """
    Retrieve extracted text content for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Extracted text content
        
    Raises:
        HTTPException: If document or extracted text not found
    """
    try:
        logger.info(f"Retrieving extracted text for document: {document_id}")
        
        # Verify document exists
        document = db_service.get_document(document_id)
        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        ensure_document_access(request=request, document=document)
        
        # Get extracted text
        extracted_text = db_service.get_document_text(document_id)
        
        if not extracted_text:
            logger.warning(f"Extracted text not found for document: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Extracted text not found for document ID {document_id}"
            )
        
        return ExtractedTextResponse.model_validate(extracted_text)
        
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Error retrieving extracted text: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving extracted text"
        )


@app.get(
    "/documents/{document_id}/full",
    response_model=DocumentWithTextResponse,
    summary="Get document with extracted text",
    tags=["Documents"]
)
async def get_document_with_text(document_id: int, request: Request) -> DocumentWithTextResponse:
    """
    Retrieve document metadata along with extracted text.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document with extracted text
        
    Raises:
        HTTPException: If document not found
    """
    try:
        logger.info(f"Retrieving full document data: {document_id}")
        
        document = db_service.get_document(document_id)
        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        ensure_document_access(request=request, document=document)
        
        extracted_text = db_service.get_document_text(document_id)
        
        return DocumentWithTextResponse(
            document=DocumentResponse.model_validate(document),
            extracted_text=ExtractedTextResponse.model_validate(extracted_text) if extracted_text else None
        )
        
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Error retrieving full document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error retrieving document"
        )


@app.get(
    "/documents",
    response_model=list[DocumentResponse],
    summary="List all documents",
    tags=["Documents"]
)
async def list_documents(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> list:
    """
    Retrieve list of all documents with pagination.
    
    Args:
        limit: Maximum number of documents to return (default: 100, max: 1000)
        offset: Number of documents to skip (default: 0)
        
    Returns:
        List of documents
    """
    try:
        logger.info(f"Listing documents: limit={limit}, offset={offset}")
        documents = db_service.get_all_documents(limit=limit, offset=offset)
        documents = [doc for doc in documents if _can_access_document(request, doc)]
        return [DocumentResponse.model_validate(doc) for doc in documents]
        
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error listing documents"
        )


# ============================================================================
# Semantic Search Endpoints
# ============================================================================

@app.post(
    "/search/document/{document_id}",
    response_model=SemanticSearchResponse,
    summary="Search within a specific document",
    tags=["Search"]
)
async def search_document(
    request: Request,
    document_id: int,
    query: str = Query(..., min_length=1, description="Search query text"),
    k: int = Query(5, ge=1, le=20, description="Number of results to return")
) -> SemanticSearchResponse:
    """
    Perform semantic search within a specific document using vector embeddings.
    
    This endpoint searches for semantically similar text chunks within a single document
    based on the provided query using FAISS vector index.
    
    Args:
        document_id: Document ID to search within
        query: Search query text (minimum 1 character)
        k: Number of results to return (default: 5, max: 20)
        
    Returns:
        Search results with ranked matches and similarity scores
        
    Raises:
        HTTPException: If document not found or search fails
    """
    try:
        logger.info(f"Searching document {document_id} with query: '{query}'")
        
        # Verify document exists
        document = db_service.get_document(document_id)
        if not document:
            logger.warning(f"Document not found for search: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        ensure_document_access(request=request, document=document)
        
        # Perform semantic search
        search_results = vector_service.search_document(
            document_id=document_id,
            query=query,
            k=k
        )
        
        if not search_results:
            logger.info(f"No results found for query in document {document_id}")
            return SemanticSearchResponse(
                success=True,
                query=query,
                num_results=0,
                results=[],
                error=None
            )
        
        # Convert search results to response format
        results = [
            SearchResult(
                rank=i + 1,
                document_id=None,  # Single-document search doesn't include doc_id
                chunk_id=result.get('chunk_id', ''),
                distance=result.get('distance', 0.0),
                similarity_score=result.get('similarity_score', 0.0)
            )
            for i, result in enumerate(search_results)
        ]
        
        logger.info(f"Search completed: found {len(results)} results in document {document_id}")
        return SemanticSearchResponse(
            success=True,
            query=query,
            num_results=len(results),
            results=results,
            error=None
        )
        
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Error during document search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during document search"
        )


@app.post(
    "/search",
    response_model=SemanticSearchResponse,
    summary="Search across all documents",
    tags=["Search"]
)
async def search_all_documents(
    request: Request,
    query: str = Query(..., min_length=1, description="Search query text"),
    document_ids: str = Query(None, description="Comma-separated document IDs to search (optional)"),
    k: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SemanticSearchResponse:
    """
    Perform semantic search across all documents (or specified documents) using vector embeddings.
    
    This endpoint searches for semantically similar text chunks across the entire document
    collection (or a subset of documents) using FAISS vector indices.
    
    Args:
        query: Search query text (minimum 1 character)
        document_ids: Optional comma-separated document IDs to limit search scope
        k: Number of results to return (default: 10, max: 50)
        
    Returns:
        Search results with ranked matches, document IDs, and similarity scores
        
    Raises:
        HTTPException: For search failures
    """
    try:
        logger.info(f"Searching all documents with query: '{query}'")
        
        # Parse document IDs if provided
        doc_ids = None
        if document_ids:
            try:
                doc_ids = [int(d.strip()) for d in document_ids.split(',') if d.strip()]
                logger.info(f"Limiting search to documents: {doc_ids}")
            except ValueError:
                logger.warning(f"Invalid document IDs format: {document_ids}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid document IDs format. Use comma-separated integers."
                )

            for doc_id in doc_ids:
                document = db_service.get_document(doc_id)
                if not document:
                    raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
                ensure_document_access(request=request, document=document)
        else:
            raise HTTPException(
                status_code=400,
                detail="document_ids is required for cross-document search",
            )
        
        # Perform cross-document semantic search
        search_results = vector_service.search_all_documents(
            query=query,
            k=k,
            document_ids=doc_ids
        )
        
        if not search_results:
            logger.info(f"No results found for query across documents")
            return SemanticSearchResponse(
                success=True,
                query=query,
                num_results=0,
                results=[],
                error=None
            )
        
        # Convert search results to response format
        results = [
            SearchResult(
                rank=i + 1,
                document_id=int(result.get('document_id', 0)),
                chunk_id=result.get('chunk_id', ''),
                distance=result.get('distance', 0.0),
                similarity_score=result.get('similarity_score', 0.0)
            )
            for i, result in enumerate(search_results)
        ]
        
        logger.info(f"Cross-document search completed: found {len(results)} results")
        return SemanticSearchResponse(
            success=True,
            query=query,
            num_results=len(results),
            results=results,
            error=None
        )
        
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Error during cross-document search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during cross-document search"
        )


# ============================================================================
# Document Health Check Endpoint
# ============================================================================

@app.get(
    "/documents/{document_id}/health",
    summary="Get document extraction health report",
    tags=["Documents"]
)
async def get_document_health(document_id: int, request: Request):
    """
    Get health assessment for document text extraction.
    
    Provides detailed metrics about the quality and integrity of extracted text,
    including character counts, word counts, encoding issues, and validation warnings.
    
    Args:
        document_id: Document ID
        
    Returns:
        Health report with metrics and warnings
        
    Raises:
        HTTPException: If document not found
    """
    try:
        logger.info(f"Generating health report for document: {document_id}")
        
        # Verify document exists
        document = db_service.get_document(document_id)
        if not document:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        ensure_document_access(request=request, document=document)
        
        # Get extracted text
        extracted_text = db_service.get_document_text(document_id)
        
        if not extracted_text:
            logger.warning(f"No extracted text found for document: {document_id}")
            return {
                "document_id": document_id,
                "filename": document.filename,
                "file_format": document.file_format,
                "extraction_status": "no_text",
                "health_score": 0,
                "message": "No extracted text found for this document"
            }
        
        # Generate health assessment
        text_to_assess = extracted_text.raw_text or ""
        health_report = text_validator.get_text_health_score(text_to_assess)
        
        return {
            "document_id": document_id,
            "filename": document.filename,
            "file_format": document.file_format,
            "extraction_status": extracted_text.extraction_status,
            "extraction_timestamp": extracted_text.extraction_timestamp,
            "health_score": health_report['score'],
            "is_valid": health_report['is_valid'],
            "metrics": {
                "length": health_report['length'],
                "word_count": health_report['word_count'],
                "line_count": health_report['line_count'],
                "unique_chars": health_report['unique_chars'],
                "null_bytes": health_report['null_bytes'],
                "control_chars": health_report['control_chars'],
                "encoding_issues": health_report['encoding_issues']
            },
            "warnings": health_report['warnings']
        }
        
    except HTTPException:
        raise
    except (RuntimeError, OSError, ValueError, SQLAlchemyError) as e:
        logger.error(f"Error generating health report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error generating health report"
        )


@app.get(
    "/system/status",
    summary="Get system status including dependencies",
    tags=["System"]
)
async def get_system_status():
    """
    Get comprehensive system status including:
    - Service version and status
    - Dependency availability
    - Format support status
    
    Returns:
        System status report
    """
    try:
        logger.info("Generating system status report...")
        
        format_support = dependency_checker.get_format_support_status()
        
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "format_support": format_support,
            "debug_mode": settings.DEBUG
        }
        
    except (RuntimeError, OSError, ValueError) as e:
        logger.error(f"Error generating system status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error generating system status"
        )


# ============================================================================

# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )
