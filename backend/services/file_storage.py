"""
File storage service module for managing persistent file storage.
Handles file saving and retrieval from disk.
"""
import os
import logging
import shutil
from pathlib import Path
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for managing file storage operations."""
    
    def __init__(self, base_path: str = settings.UPLOAD_DIR):
        """
        Initialize file storage service.
        
        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"File storage service initialized with base path: {self.base_path}")
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to avoid conflicts.
        
        Args:
            original_filename: Original uploaded filename
            
        Returns:
            Unique filename with timestamp
        """
        name, ext = os.path.splitext(original_filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        unique_filename = f"{name}_{timestamp}{ext}"
        return unique_filename
    
    def save_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Save uploaded file to disk storage.
        
        Args:
            file_content: File content as bytes
            original_filename: Original filename
            
        Returns:
            Path where file was saved (relative to uploads directory)
            
        Raises:
            Exception: If file save operation fails
        """
        try:
            # Generate unique filename to prevent overwrites
            unique_filename = self.generate_unique_filename(original_filename)
            file_path = self.base_path / unique_filename
            
            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File saved successfully: {file_path}")
            # Return relative path for database storage
            return str(file_path.relative_to(Path.cwd()))
            
        except IOError as e:
            logger.error(f"IO error while saving file: {str(e)}")
            raise Exception(f"Failed to save file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while saving file: {str(e)}")
            raise Exception(f"Unexpected error saving file: {str(e)}")
    
    def read_file(self, file_path: str) -> bytes:
        """
        Read file from disk storage.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as bytes
            
        Raises:
            Exception: If file read operation fails
        """
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"File read successfully: {file_path}")
            return content
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            raise
        except IOError as e:
            logger.error(f"IO error while reading file: {str(e)}")
            raise Exception(f"Failed to read file: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk storage.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deletion was successful
            
        Raises:
            Exception: If deletion fails
        """
        try:
            full_path = Path(file_path)
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted successfully: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists, False otherwise
        """
        return Path(file_path).exists()


# Global file storage service instance
file_storage = FileStorageService()
