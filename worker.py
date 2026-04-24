"""
Celery worker startup module.
Use: celery -A worker.celery_app worker --loglevel=info
"""
from celery_app import celery_app
from config import settings

# Configure structured JSON logging before any task module is imported so
# that all worker log output is machine-parseable from startup.
# analysis_tasks also calls configure_logging, but doing it here first
# ensures it applies even if tasks are imported by other means.
from services.logging_config import configure_logging
configure_logging(log_dir=settings.LOG_DIR, log_level=settings.LOG_LEVEL)

# Import tasks so Celery can discover and register them.
from services import analysis_tasks  # noqa: F401
