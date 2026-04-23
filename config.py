"""
Configuration settings for the document management service.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    ALLOWED_FORMATS: str = "pdf,docx,png,txt"
    
    # Logging Settings
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"

    # Authentication / Authorization Settings
    AUTH_SECRET: str = ""
    AUTH_COOKIE_NAME: str = "taqim_session"
    AUTH_REQUIRED: bool = True
    CLIENT_ALLOWED_PROPERTY_IDS: str = ""

    # Async Analysis Settings
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    ANALYSIS_MODULE_TIMEOUT_SECONDS: int = 90

    # Performance / Runtime Safety
    VECTOR_INDEX_MAX_LOADED_INDICES: int = 64
    VECTOR_SEARCH_PREFILTER_MIN_DOCS: int = 16
    VECTOR_SEARCH_PREFILTER_MULTIPLIER: int = 4
    VECTOR_SEARCH_PREFILTER_MIN_CANDIDATES: int = 20
    SKIP_DEPENDENCY_CHECK: bool = False

    # OpenAI Analysis Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5"
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_TIMEOUT_SECONDS: int = 120
    ANTHROPIC_API_KEY: Optional[str] = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


# Create global settings instance
settings = Settings()

# Create necessary directories
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
