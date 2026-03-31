"""
Celery worker startup module.
Use: celery -A worker.celery_app worker --loglevel=info
"""
from celery_app import celery_app

# Import tasks so Celery can discover and register them.
from services import analysis_tasks  # noqa: F401
