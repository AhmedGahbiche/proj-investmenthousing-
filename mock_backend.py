"""
Mock backend server for frontend development and testing.
Provides a lightweight FastAPI server that mimics the real backend API
without requiring PostgreSQL, Redis, or heavy ML dependencies.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os
import requests
from pathlib import Path

# ============================================================================
# API Configuration
# ============================================================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "k-proj-NxFOOs4y-9GRXerFat5qB7v-fNpVFFQdqJHxAyrD98HxvPCd5MbkUJZMipSkvdVqVlPlhgbBZmT3BlbkFJmdTDTSIGkHN6J3bArls-eRYz6v32P6051ZgnKz6GqIShH3y_zQdN1IBaqGRaqPkvRk3mmMD70A")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="Document Analysis API (Mock)",
    version="1.0.0",
    description="Mock backend for document management system"
)

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class UploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class Document(BaseModel):
    id: int
    filename: str
    file_format: str
    file_size: int
    upload_timestamp: str
    document_type: Optional[str] = None
    property_id: Optional[str] = None


class ExtractedText(BaseModel):
    id: int
    document_id: int
    raw_text: str
    extraction_timestamp: str
    extraction_status: str = "success"  # "success" | "failed" | "partial"
    extraction_error: Optional[str] = None


class SearchResult(BaseModel):
    document_id: int
    filename: str
    similarity_score: float
    excerpt: str


class HealthCheck(BaseModel):
    status: str
    timestamp: str


class SystemStatus(BaseModel):
    status: str
    database: str
    cache: str
    message_queue: str
    timestamp: str


class AnalysisOutput(BaseModel):
    legal_json: Optional[dict] = None
    risk_json: Optional[dict] = None
    valuation_json: Optional[dict] = None
    final_json: Optional[dict] = None


class AnalysisCreateResponse(BaseModel):
    success: bool
    analysis_id: int
    document_id: int
    status: str
    task_id: Optional[str] = None


class AnalysisStatus(BaseModel):
    analysis_id: int
    document_id: int
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    model_version: Optional[str] = None
    outputs: Optional[AnalysisOutput] = None


# ============================================================================
# Global Storage (In-Memory)
# ============================================================================

documents_db = {}
extracted_texts_db = {}
analysis_db = {}  # Store analysis results
next_document_id = 1
next_analysis_id = 1
uploads_dir = Path("./mock_uploads")
uploads_dir.mkdir(exist_ok=True)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@app.get("/system/status")
async def system_status():
    """Get system status"""
    return SystemStatus(
        status="operational",
        database="mock (in-memory)",
        cache="mock (in-memory)",
        message_queue="mock (in-memory)",
        timestamp=datetime.now().isoformat()
    )


# ============================================================================
# Document Upload Endpoint
# ============================================================================

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document file"""
    global next_document_id
    
    try:
        # Validate file type
        allowed_types = {".pdf", ".docx", ".png", ".txt"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if file_size > 50 * 1024 * 1024:  # 50 MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 50 MB limit")
        
        # Save file
        file_path = uploads_dir / f"{next_document_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create document record
        doc_id = next_document_id
        next_document_id += 1
        
        # Extract file extension without dot
        file_format = file_ext.lstrip('.')
        
        doc = {
            "id": doc_id,
            "filename": file.filename,
            "file_format": file_format,
            "file_size": file_size,
            "upload_timestamp": datetime.now().isoformat(),
            "document_type": None,
            "property_id": None,
            "file_path": str(file_path)
        }
        
        documents_db[doc_id] = doc
        
        # Mock: Simulate text extraction
        mock_text = f"Extracted text from {file.filename}. This is a mock extraction for demonstration purposes."
        extracted_texts_db[doc_id] = {
            "id": doc_id,
            "document_id": doc_id,
            "raw_text": mock_text,
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_status": "success",
            "extraction_error": None
        }
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded {file.filename}",
            document_id=doc_id,
            filename=file.filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return UploadResponse(
            success=False,
            message="Upload failed",
            error=str(e)
        )


# ============================================================================
# Document Retrieval Endpoints
# ============================================================================

@app.get("/documents")
async def list_documents(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """List all uploaded documents"""
    docs = list(documents_db.values())
    return docs[skip:skip + limit]


@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    """Get document details"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return documents_db[document_id]


@app.get("/documents/{document_id}/text")
async def get_extracted_text(document_id: int):
    """Get extracted text from a document"""
    if document_id not in extracted_texts_db:
        raise HTTPException(status_code=404, detail="Text not found")
    
    return extracted_texts_db[document_id]


class DocumentWithTextResponse(BaseModel):
    document: Document
    extracted_text: Optional[ExtractedText] = None


@app.get("/documents/{document_id}/full")
async def get_full_document(document_id: int):
    """Get full document with extracted text"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = documents_db[document_id]
    extracted_text = extracted_texts_db.get(document_id)
    
    return DocumentWithTextResponse(
        document=Document(**doc_data),
        extracted_text=ExtractedText(**extracted_text) if extracted_text else None
    )


# ============================================================================
# Search Endpoint
# ============================================================================

@app.post("/search/semantic")
async def semantic_search(query: str = Query(...)):
    """Perform semantic search across documents"""
    results = []
    
    # Mock search: simple keyword matching
    query_lower = query.lower()
    for doc_id, doc in documents_db.items():
        if query_lower in doc["filename"].lower():
            results.append(SearchResult(
                document_id=doc_id,
                filename=doc["filename"],
                similarity_score=0.85,
                excerpt=f"Found in {doc['filename']}"
            ))
    
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }


@app.post("/documents/{document_id}/search")
async def search_document(document_id: int, query: str = Query(...)):
    """Search within a specific document"""
    if document_id not in extracted_texts_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    text = extracted_texts_db[document_id]["raw_text"]
    query_lower = query.lower()
    
    if query_lower in text.lower():
        return {
            "document_id": document_id,
            "query": query,
            "found": True,
            "matches": 1
        }
    
    return {
        "document_id": document_id,
        "query": query,
        "found": False,
        "matches": 0
    }


# ============================================================================
# Analysis Endpoints
# ============================================================================

class AnalyzeRequest(BaseModel):
    document_id: int
    model_version: Optional[str] = None


def analyze_with_claude(text: str) -> dict:
    """Call Claude API to analyze document text"""
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Prepare analysis prompt
        doc_text = text[:2000] if text else "No text available"
        analysis_prompt = f"""You are an expert document analyzer. Analyze the following document text and provide:

1. A legal analysis in JSON format with keys: risk_level (low/medium/high), summary, flags (array of issues)
2. A risk analysis in JSON format with keys: overall_risk_score (0-10), risk_level, identified_risks (array with type, description, severity)
3. A valuation analysis in JSON format with keys: estimated_value (number), confidence_score (0-1), valuation_method

Document text:
{doc_text}

Respond with valid JSON containing exactly three keys: "legal_json", "risk_json", "valuation_json" """
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ]
        }
        
        response = requests.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            error_msg = response.text
            print(f"Claude API error: {response.status_code} - {error_msg}")
            # Log to file for debugging
            with open("api_errors.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - Status: {response.status_code} - {error_msg}\n")
            return None
        
        response_data = response.json()
        content = response_data.get("content", [{}])[0].get("text", "{}")
        
        print(f"Claude API success. Response length: {len(content)}")
        
        # Parse the JSON response
        try:
            # Try to extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            analysis = json.loads(content)
            print(f"Successfully parsed analysis: {list(analysis.keys())}")
            return analysis
        except json.JSONDecodeError as e:
            print(f"Failed to parse Claude response: {str(e)}")
            print(f"Response content: {content[:500]}")
            return None
    
    except requests.exceptions.Timeout:
        print("Claude API request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print("Claude API connection error")
        return None
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        return None


def get_mock_analysis() -> dict:
    """Return mock analysis when API fails"""
    return {
        "legal_json": {
            "risk_level": "low",
            "summary": "Standard document with market-rate provisions.",
            "flags": []
        },
        "risk_json": {
            "overall_risk_score": 2.5,
            "risk_level": "low",
            "identified_risks": [
                {
                    "type": "standard",
                    "description": "Standard market terms",
                    "severity": "low"
                }
            ]
        },
        "valuation_json": {
            "estimated_value": 0,
            "confidence_score": 0.0,
            "valuation_method": "mock"
        }
    }

@app.post("/analyze")
async def create_analysis(request: AnalyzeRequest):
    """Create analysis for a document"""
    global next_analysis_id
    
    document_id = request.document_id
    
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get extracted text
    extracted_text = extracted_texts_db.get(document_id)
    if not extracted_text:
        raise HTTPException(status_code=404, detail="No extracted text found")
    
    # Call Claude API to analyze the text
    text_to_analyze = extracted_text.get("raw_text", "")
    analysis_results = analyze_with_claude(text_to_analyze)
    
    # Use mock analysis if Claude API fails
    if analysis_results is None:
        analysis_results = get_mock_analysis()
    
    # Create analysis record
    analysis_id = next_analysis_id
    next_analysis_id += 1
    
    analysis = {
        "analysis_id": analysis_id,
        "document_id": document_id,
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "finished_at": datetime.now().isoformat(),
        "outputs": {
            "legal_json": analysis_results.get("legal_json", {}),
            "risk_json": analysis_results.get("risk_json", {}),
            "valuation_json": analysis_results.get("valuation_json", {})
        }
    }
    
    analysis_db[analysis_id] = analysis
    
    return AnalysisCreateResponse(
        success=True,
        analysis_id=analysis_id,
        document_id=document_id,
        status="completed"
    )


@app.get("/analyze/{analysis_id}")
async def get_analysis_status(analysis_id: int):
    """Get analysis status"""
    if analysis_id not in analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_db[analysis_id]
    return AnalysisStatus(
        analysis_id=analysis_id,
        document_id=analysis["document_id"],
        status=analysis["status"],
        started_at=analysis.get("started_at"),
        finished_at=analysis.get("finished_at"),
        error=analysis.get("error"),
        model_version="mock-1.0",
        outputs=AnalysisOutput(**analysis["outputs"]) if analysis.get("outputs") else None
    )


# ============================================================================
# Startup Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("✓ Mock Backend Server Started")
    print(f"  - API running on: http://localhost:8000")
    print(f"  - Health check: GET /health")
    print(f"  - Swagger UI: GET /docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
