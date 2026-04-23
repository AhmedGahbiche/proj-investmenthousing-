"""
Upload service module for handling file upload validation and orchestration.
Coordinates file storage, text extraction, and database operations.
"""
import logging
from threading import Lock
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from config import settings
from services.file_storage import file_storage, FileStorageError
from services.text_extraction import text_extraction
from services.database import db_service
from services.vector_service import vector_service

logger = logging.getLogger(__name__)


_upload_service_instance: Optional["UploadService"] = None
_upload_service_lock = Lock()


class UploadService:
    """Service for handling document uploads and processing."""
    
    def __init__(self):
        """Initialize upload service."""
        if isinstance(settings.ALLOWED_FORMATS, str):
            self.allowed_formats = [f.strip().lower() for f in settings.ALLOWED_FORMATS.split(',') if f.strip()]
        else:
            self.allowed_formats = [str(f).strip().lower() for f in settings.ALLOWED_FORMATS]
        self.max_file_size = settings.MAX_FILE_SIZE
        # MIME type to format mapping
        self.mime_to_format = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'image/png': 'png',
            'text/plain': 'txt',
        }
    
    def validate_file(
        self,
        filename: str,
        file_content: bytes,
        content_type: str = None
    ) -> tuple[bool, str]:
        """
        Validate uploaded file.
        
        Args:
            filename: Original filename
            file_content: File content as bytes
            content_type: MIME type of the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate filename
        if not filename or not filename.strip():
            return False, "Filename is empty"
        
        # Extract file extension
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if not file_ext:
            return False, "File has no extension"
        
        # Validate file extension
        if file_ext not in self.allowed_formats:
            return False, f"File format '.{file_ext}' is not supported. Allowed formats: {', '.join(self.allowed_formats)}"
        
        # Validate file size
        file_size = len(file_content)
        if file_size == 0:
            return False, "File is empty"
        
        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size ({max_size_mb} MB)"
        
        logger.info(f"File validation passed: {filename} ({file_size} bytes)")
        return True, ""

    def _build_result(
        self,
        success: bool,
        filename: str,
        message: str,
        document_id: int = None,
        error: str = None,
    ) -> dict:
        """Build a normalized upload response payload."""
        return {
            'success': success,
            'document_id': document_id,
            'filename': filename,
            'message': message,
            'error': error,
        }

    def _store_file(self, filename: str, file_content: bytes) -> str:
        """Persist uploaded content to storage and return its relative path."""
        logger.info(f"Saving file to disk: {filename}")
        return file_storage.save_file(file_content, filename)

    def _save_document_metadata(
        self,
        filename: str,
        file_ext: str,
        file_path: str,
        file_size: int,
        document_type: str,
        property_id: str,
    ):
        """Save document metadata to the database."""
        logger.info(f"Saving document metadata to database: {filename}")
        return db_service.save_document(
            filename=filename,
            file_format=file_ext,
            file_path=file_path,
            file_size=file_size,
            document_type=document_type,
            property_id=property_id,
        )

    def _extract_document_text(self, filename: str, file_path: str, file_ext: str) -> tuple[str, str, str]:
        """Extract text and normalize extraction failures into a status payload."""
        logger.info(f"Extracting text from document: {filename}")
        try:
            return text_extraction.extract_text(file_path, file_ext)
        except (ValueError, RuntimeError, OSError, TimeoutError) as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return "", "failed", str(e)

    def _save_extracted_text(
        self,
        filename: str,
        document_id: int,
        raw_text: str,
        extraction_status: str,
        extraction_error: str,
    ) -> None:
        """Persist extracted text for the uploaded document."""
        logger.info(f"Saving extracted text to database: {filename}")
        db_service.save_extracted_text(
            document_id=document_id,
            raw_text=raw_text if raw_text else "",
            extraction_status=extraction_status,
            extraction_error=extraction_error,
        )

    def _generate_embeddings(self, filename: str, document_id: int, raw_text: str, extraction_status: str) -> Optional[str]:
        """Generate embeddings and return an optional non-fatal error message."""
        logger.info(f"Generating vector embeddings for document: {filename}")
        try:
            if raw_text and extraction_status == "success":
                vector_service.embed_document(
                    document_id=document_id,
                    text=raw_text,
                    chunk_size=512,
                    overlap=50,
                )

                try:
                    db_service.save_vector_embedding_metadata(
                        document_id=document_id,
                        num_chunks=vector_service.vector_index.get_index_stats(document_id)['num_vectors'],
                    )
                except (ValueError, RuntimeError, OSError, SQLAlchemyError) as e:
                    logger.warning(f"Failed to save embedding metadata for document {document_id}: {str(e)}")
            else:
                logger.warning(f"Skipping embedding for document {document_id}: no text extracted")
            return None
        except (ValueError, RuntimeError, OSError) as e:
            logger.warning(f"Vector embedding failed for document {document_id}: {str(e)}")
            return "Vector indexing skipped due to a processing error"
    
    def process_upload(
        self,
        filename: str,
        file_content: bytes,
        document_type: str = None,
        property_id: str = None
    ) -> dict:
        """
        Process file upload end-to-end.
        
        Orchestrates: validation -> storage -> text extraction -> database persistence
        
        Args:
            filename: Original filename
            file_content: File content as bytes
            document_type: Optional document type classification
            property_id: Optional property ID reference
            
        Returns:
            Dictionary with upload result:
            {
                'success': bool,
                'document_id': int or None,
                'filename': str,
                'message': str,
                'error': str or None
            }
        """
        try:
            logger.info(f"Starting upload process for: {filename}")
            is_valid, error_msg = self.validate_file(filename, file_content)

            if not is_valid:
                logger.warning(f"File validation failed: {error_msg}")
                return self._build_result(
                    success=False,
                    filename=filename,
                    message='File validation failed',
                    error=error_msg,
                )

            file_ext = filename.rsplit('.', 1)[-1].lower()
            file_size = len(file_content)

            try:
                file_path = self._store_file(filename, file_content)
            except (ValueError, FileStorageError) as e:
                logger.error(f"File storage failed: {str(e)}")
                return self._build_result(
                    success=False,
                    filename=filename,
                    message='Failed to save file to storage',
                    error='Storage service error',
                )

            try:
                document = self._save_document_metadata(
                    filename=filename,
                    file_ext=file_ext,
                    file_path=file_path,
                    file_size=file_size,
                    document_type=document_type,
                    property_id=property_id,
                )
            except (SQLAlchemyError, ValueError, RuntimeError) as e:
                logger.error(f"Database save failed: {str(e)}")
                try:
                    file_storage.delete_file(file_path)
                except FileStorageError as cleanup_error:
                    logger.warning(
                        "Cleanup after database save failure did not remove file '%s': %s",
                        file_path,
                        str(cleanup_error),
                    )
                return self._build_result(
                    success=False,
                    filename=filename,
                    message='Failed to save document to database',
                    error='Database service error',
                )

            raw_text, extraction_status, extraction_error = self._extract_document_text(
                filename=filename,
                file_path=file_path,
                file_ext=file_ext,
            )

            try:
                self._save_extracted_text(
                    filename=filename,
                    document_id=document.id,
                    raw_text=raw_text,
                    extraction_status=extraction_status,
                    extraction_error=extraction_error,
                )
            except (SQLAlchemyError, ValueError, RuntimeError) as e:
                logger.error(f"Failed to save extracted text: {str(e)}")
                return self._build_result(
                    success=True,
                    filename=filename,
                    document_id=document.id,
                    message='Document saved but text extraction failed',
                    error='Text extraction persistence error',
                )

            embedding_error = self._generate_embeddings(
                filename=filename,
                document_id=document.id,
                raw_text=raw_text,
                extraction_status=extraction_status,
            )

            logger.info(f"Upload process completed successfully for: {filename} (ID: {document.id})")
            return self._build_result(
                success=True,
                filename=filename,
                document_id=document.id,
                message='Document uploaded and processed successfully',
                error=embedding_error,
            )

        except (ValueError, RuntimeError, OSError, SQLAlchemyError, FileStorageError) as e:
            logger.error(f"Unexpected error during upload processing: {str(e)}")
            return self._build_result(
                success=False,
                filename=filename,
                message='Unexpected error during upload processing',
                error='Internal upload processing error',
            )


def get_upload_service() -> "UploadService":
    """Return a lazily initialized singleton upload service instance."""
    global _upload_service_instance
    if _upload_service_instance is None:
        with _upload_service_lock:
            if _upload_service_instance is None:
                _upload_service_instance = UploadService()
    return _upload_service_instance


class _LazyUploadServiceProxy:
    """Compatibility proxy to keep existing `upload_service.*` call sites unchanged."""

    def __getattr__(self, name):
        return getattr(get_upload_service(), name)


# Lazy upload service proxy (keeps import API stable)
upload_service = _LazyUploadServiceProxy()
