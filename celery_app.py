"""
Celery application configuration for asynchronous analysis tasks.
"""
from celery import Celery
from celery.schedules import crontab
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

    # Acknowledge tasks only after they complete, not when dequeued.
    # This ensures a worker crash or OOM-kill causes the broker to redeliver
    # the task rather than silently losing it.
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Cap prefetch to 1 so a busy worker does not hoard unacknowledged tasks.
    # Without this, acks_late provides less protection because multiple tasks
    # are dequeued but unfinished on a single worker.
    worker_prefetch_multiplier=1,

    # Periodic watchdog: promotes analyses stuck in 'queued' or 'processing'
    # beyond the stale threshold to 'failed' so operators can act on them.
    beat_schedule={
        "promote-stuck-analyses": {
            "task": "services.analysis_tasks.promote_stuck_analyses",
            "schedule": crontab(minute="*/10"),  # every 10 minutes
        },
    },
)
