"""
Configuration settings for the document management service.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


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

    # Async Analysis Settings
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # OpenAI Analysis Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5"
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_TIMEOUT_SECONDS: int = 120
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Create necessary directories
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
