"""
Configuration settings for the document management service.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or defaults."""
    
    # FastAPI Settings
    APP_NAME: str = "Document Management Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/document_management"
    
    # File Storage Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_FORMATS: list = ["pdf", "docx", "png", "txt"]
    
    # Logging Settings
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Create necessary directories
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
