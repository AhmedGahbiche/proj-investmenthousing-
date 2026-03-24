"""
Celery application configuration for asynchronous analysis tasks.
"""
from celery import Celery
from config import settings

celery_app = Celery(
    "document_analysis",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
