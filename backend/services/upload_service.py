"""
Upload service module for handling file upload validation and orchestration.
Coordinates file storage, text extraction, and database operations.
"""
import logging
from mimetypes import guess_extension
from config import settings
from services.file_storage import file_storage
from services.text_extraction import text_extraction
from services.database import db_service
from services.vector_service import vector_service

logger = logging.getLogger(__name__)


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
            # Step 1: Validate file
            logger.info(f"Starting upload process for: {filename}")
            is_valid, error_msg = self.validate_file(filename, file_content)
            
            if not is_valid:
                logger.warning(f"File validation failed: {error_msg}")
                return {
                    'success': False,
                    'document_id': None,
                    'filename': filename,
                    'message': 'File validation failed',
                    'error': error_msg
                }
            
            # Extract file extension and size
            file_ext = filename.rsplit('.', 1)[-1].lower()
            file_size = len(file_content)
            
            # Step 2: Save file to disk
            logger.info(f"Saving file to disk: {filename}")
            try:
                file_path = file_storage.save_file(file_content, filename)
            except Exception as e:
                logger.error(f"File storage failed: {str(e)}")
                return {
                    'success': False,
                    'document_id': None,
                    'filename': filename,
                    'message': 'Failed to save file to storage',
                    'error': str(e)
                }
            
            # Step 3: Save document metadata to database
            logger.info(f"Saving document metadata to database: {filename}")
            try:
                document = db_service.save_document(
                    filename=filename,
                    file_format=file_ext,
                    file_path=file_path,
                    file_size=file_size,
                    document_type=document_type,
                    property_id=property_id
                )
            except Exception as e:
                logger.error(f"Database save failed: {str(e)}")
                # Attempt to clean up saved file
                try:
                    file_storage.delete_file(file_path)
                except:
                    pass
                return {
                    'success': False,
                    'document_id': None,
                    'filename': filename,
                    'message': 'Failed to save document to database',
                    'error': str(e)
                }
            
            # Step 4: Extract text from document
            logger.info(f"Extracting text from document: {filename}")
            try:
                raw_text, extraction_status, extraction_error = text_extraction.extract_text(
                    file_path,
                    file_ext
                )
            except Exception as e:
                raw_text, extraction_status, extraction_error = "", "failed", str(e)
                logger.error(f"Text extraction failed: {str(e)}")
            
            # Step 5: Save extracted text to database
            logger.info(f"Saving extracted text to database: {filename}")
            try:
                extracted_text = db_service.save_extracted_text(
                    document_id=document.id,
                    raw_text=raw_text if raw_text else "",
                    extraction_status=extraction_status,
                    extraction_error=extraction_error
                )
            except Exception as e:
                logger.error(f"Failed to save extracted text: {str(e)}")
                # Return success for document even if text extraction failed
                return {
                    'success': True,
                    'document_id': document.id,
                    'filename': filename,
                    'message': 'Document saved but text extraction failed',
                    'error': f"Text extraction error: {str(e)}"
                }
            
            # Step 6: Generate vector embeddings for semantic search
            logger.info(f"Generating vector embeddings for document: {filename}")
            embedding_error = None
            try:
                if raw_text and extraction_status == "success":
                    # Create embeddings and store in FAISS index
                    vector_service.embed_document(
                        document_id=document.id,
                        text=raw_text,
                        chunk_size=512,
                        overlap=50
                    )
                    
                    # Save embedding metadata to database
                    try:
                        db_service.save_vector_embedding_metadata(
                            document_id=document.id,
                            num_chunks=vector_service.vector_index.get_index_stats(document.id)['num_vectors']
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save embedding metadata for document {document.id}: {str(e)}")
                else:
                    logger.warning(f"Skipping embedding for document {document.id}: no text extracted")
            except Exception as e:
                logger.warning(f"Vector embedding failed for document {document.id}: {str(e)}")
                embedding_error = str(e)
                # Don't fail the entire upload, just log the warning
            
            logger.info(f"Upload process completed successfully for: {filename} (ID: {document.id})")
            return {
                'success': True,
                'document_id': document.id,
                'filename': filename,
                'message': 'Document uploaded and processed successfully',
                'error': embedding_error
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during upload processing: {str(e)}")
            return {
                'success': False,
                'document_id': None,
                'filename': filename,
                'message': 'Unexpected error during upload processing',
                'error': str(e)
            }


# Global upload service instance
upload_service = UploadService()
