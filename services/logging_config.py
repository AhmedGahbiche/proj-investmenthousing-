"""
Structured JSON logging configuration shared by the API and Celery worker.

Every log record is emitted as a single JSON line with a stable set of fields
so log aggregators (Loki, Datadog, CloudWatch Logs Insights) can index and
filter without regex parsing.

Standard fields on every record:
    timestamp   ISO-8601 UTC
    level       DEBUG / INFO / WARNING / ERROR / CRITICAL
    logger      logger name (e.g. "services.analysis_tasks")
    message     the formatted log message
    process     OS PID
    thread      thread name

Optional context fields injected by filters:
    request_id  UUID set by RequestIdMiddleware for API requests
    analysis_id int set by AnalysisLogContext for worker tasks
"""
import json
import logging
import logging.handlers
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


# Thread-local storage for per-request / per-task context fields.
_log_context = threading.local()


def set_log_context(**kwargs):
    """Set key-value pairs on the current thread's log context."""
    for k, v in kwargs.items():
        setattr(_log_context, k, v)


def clear_log_context(*keys):
    """Remove specific keys (or all) from the current thread's log context."""
    if keys:
        for k in keys:
            _log_context.__dict__.pop(k, None)
    else:
        _log_context.__dict__.clear()


class _ContextFilter(logging.Filter):
    """Inject thread-local context fields into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in _log_context.__dict__.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


class _JsonFormatter(logging.Formatter):
    """Format a LogRecord as a single UTF-8 JSON line."""

    # Fields pulled from LogRecord that are included unconditionally.
    _CORE_FIELDS = ("levelname", "name", "process", "threadName")

    # Context fields that are included only when present.
    _CONTEXT_FIELDS = ("request_id", "analysis_id")

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.threadName,
        }

        for field in self._CONTEXT_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(log_dir: str, log_level: str = "INFO") -> None:
    """
    Configure root logger with JSON output to stdout and a rotating file.

    Calling this replaces any handlers previously set on the root logger,
    including the ad-hoc setup in main.py. Safe to call multiple times
    (idempotent — checks for existing _JsonFormatter handlers first).

    Args:
        log_dir: Directory for the rotating file handler.
        log_level: Logging level name (INFO, DEBUG, etc.).
    """
    root = logging.getLogger()

    # Avoid double-configuring when called from multiple entry points.
    if any(isinstance(h.formatter, _JsonFormatter) for h in root.handlers):
        return

    root.handlers.clear()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    context_filter = _ContextFilter()
    formatter = _JsonFormatter()

    # Stdout handler — consumed by Docker / log forwarder.
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(context_filter)
    root.addHandler(stdout_handler)

    # Rotating file handler — local fallback / developer convenience.
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        Path(log_dir) / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)
    root.addHandler(file_handler)

    # Suppress noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "openai._base_client", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
