"""
Asynchronous analysis tasks.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from celery_app import celery_app
from config import settings
from services.database import db_service
from services.regulation_retrieval import regulation_retrieval_service
from services.analysis_intelligence import analysis_intelligence_service
from services.logging_config import configure_logging, set_log_context, clear_log_context

# Ensure worker processes emit structured JSON logs using the same config as the API.
configure_logging(log_dir=settings.LOG_DIR, log_level=settings.LOG_LEVEL)

# How long (minutes) a processing analysis may run before the watchdog flags it.
_PROCESSING_STUCK_THRESHOLD_MINUTES = 30

logger = logging.getLogger(__name__)


def _resolve_module_result(analysis_id: int, module_name: str, future):
    """Resolve a module future with timeout and partial-failure fallback payload."""
    timeout_seconds = settings.ANALYSIS_MODULE_TIMEOUT_SECONDS
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        message = f"{module_name} timed out after {timeout_seconds}s"
    except Exception as exc:
        message = f"{module_name} failed: {str(exc)}"

    logger.warning("Analysis module warning for analysis_id=%s: %s", analysis_id, message)
    db_service.add_analysis_event(
        analysis_id,
        stage=f"{module_name}_warning",
        payload={"warning": message},
    )
    return {
        "status": "partial",
        "error": message,
    }


def _run_analysis_pipeline(analysis_id: int, document_text: str) -> dict:
    """Run retrieval, module scoring, and final synthesis for a text payload."""
    query_seed = document_text[:2000]

    db_service.add_analysis_event(analysis_id, stage="retrieval_started")
    contexts = regulation_retrieval_service.retrieve_context(query=query_seed, k=5)
    db_service.add_analysis_event(
        analysis_id,
        stage="retrieval_completed",
        payload={"context_count": len(contexts)},
    )

    db_service.add_analysis_event(analysis_id, stage="scoring_started")
    with ThreadPoolExecutor(max_workers=3) as executor:
        legal_future = executor.submit(
            analysis_intelligence_service.legal_analysis,
            document_text,
            contexts,
        )
        risk_future = executor.submit(
            analysis_intelligence_service.risk_analysis,
            document_text,
            contexts,
        )
        valuation_future = executor.submit(
            analysis_intelligence_service.valuation_analysis,
            document_text,
            contexts,
        )

        legal_json = _resolve_module_result(analysis_id, "legal_analysis", legal_future)
        db_service.save_module_output(analysis_id, "legal", legal_json)

        risk_json = _resolve_module_result(analysis_id, "risk_analysis", risk_future)
        db_service.save_module_output(analysis_id, "risk", risk_json)

        valuation_json = _resolve_module_result(analysis_id, "valuation_analysis", valuation_future)
        db_service.save_module_output(analysis_id, "valuation", valuation_json)

    db_service.add_analysis_event(analysis_id, stage="final_synthesis_started")
    final_json = analysis_intelligence_service.final_due_diligence(
        document_text=document_text,
        contexts=contexts,
        legal_json=legal_json,
        risk_json=risk_json,
        valuation_json=valuation_json,
    )

    # Frontend contract expects a direct report URL once outputs are available.
    if isinstance(final_json, dict):
        final_json.setdefault("report_url", f"/reports/{analysis_id}/html")

    # Checkpoint final synthesis result; individual module columns already persisted above.
    db_service.save_module_output(analysis_id, "final", final_json)
    db_service.add_analysis_event(analysis_id, stage="outputs_saved")

    db_service.update_analysis_status(analysis_id, status="completed")
    db_service.add_analysis_event(analysis_id, stage="processing_completed")

    return final_json


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_analysis_task(self, document_id: int, analysis_id: int):
    """
    Run document analysis asynchronously with retries and status tracking.
    """
    set_log_context(analysis_id=analysis_id)
    try:
        db_service.update_analysis_status(analysis_id, status="processing")
        db_service.add_analysis_event(analysis_id, stage="processing_started")

        extracted_text = db_service.get_document_text(document_id)
        if not extracted_text or not extracted_text.raw_text.strip():
            raise ValueError("No extracted text available for analysis")

        final_json = _run_analysis_pipeline(
            analysis_id=analysis_id,
            document_text=extracted_text.raw_text,
        )

        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "overall_score": final_json.get("overall_score"),
        }

    except Exception as exc:
        logger.exception("Analysis task failed for analysis_id=%s", analysis_id)
        db_service.add_analysis_event(
            analysis_id,
            stage="processing_error",
            payload={"error": str(exc)},
        )

        if self.request.retries >= self.max_retries:
            db_service.update_analysis_status(
                analysis_id,
                status="failed",
                error=str(exc),
            )
            return {
                "analysis_id": analysis_id,
                "status": "failed",
                "error": str(exc),
            }

        raise self.retry(exc=exc)
    finally:
        clear_log_context("analysis_id")


@celery_app.task(name="services.analysis_tasks.promote_stuck_analyses")
def promote_stuck_analyses():
    """
    Beat-scheduled watchdog that marks hopelessly stuck analyses as failed.

    Runs every 10 minutes (configured in celery_app.py beat_schedule).

    'queued' analyses with no started_at have been abandoned by the broker —
    either a pre-acks_late drop or an enqueue that never reached a worker.
    With acks_late now enabled these should be rare, but we still detect them
    to cover the transition period and operator-triggered retries.

    'processing' analyses past the threshold had their worker crash or get
    OOM-killed after the task was acknowledged; they will never self-resolve.
    """
    stuck = db_service.get_stuck_analyses(
        processing_threshold_minutes=_PROCESSING_STUCK_THRESHOLD_MINUTES,
    )
    if not stuck:
        logger.info("promote_stuck_analyses: no stuck analyses found")
        return {"promoted": 0}

    promoted = 0
    for analysis in stuck:
        try:
            db_service.update_analysis_status(
                analysis.id,
                status="failed",
                error=f"Promoted to failed by watchdog: was stuck in '{analysis.status}'",
            )
            db_service.add_analysis_event(
                analysis.id,
                stage="watchdog_promoted_failed",
                payload={
                    "previous_status": analysis.status,
                    "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
                },
            )
            logger.warning(
                "promote_stuck_analyses: promoted analysis_id=%s from '%s' to 'failed'",
                analysis.id,
                analysis.status,
            )
            promoted += 1
        except Exception:
            logger.exception("promote_stuck_analyses: failed to promote analysis_id=%s", analysis.id)

    return {"promoted": promoted}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_property_analysis_task(self, document_ids: list[int], analysis_id: int):
    """Run one combined analysis over multiple document texts."""
    set_log_context(analysis_id=analysis_id)
    try:
        db_service.update_analysis_status(analysis_id, status="processing")
        db_service.add_analysis_event(
            analysis_id,
            stage="processing_started",
            payload={"document_ids": document_ids},
        )

        extracted_parts = []
        for document_id in document_ids:
            extracted_text = db_service.get_document_text(document_id)
            if extracted_text and extracted_text.raw_text and extracted_text.raw_text.strip():
                extracted_parts.append(f"[Document {document_id}]\n{extracted_text.raw_text}")

        if not extracted_parts:
            raise ValueError("No extracted text available for property analysis")

        combined_text = "\n\n".join(extracted_parts)
        final_json = _run_analysis_pipeline(
            analysis_id=analysis_id,
            document_text=combined_text,
        )

        return {
            "analysis_id": analysis_id,
            "status": "completed",
            "overall_score": final_json.get("overall_score") if isinstance(final_json, dict) else None,
            "documents_analyzed": len(document_ids),
        }

    except Exception as exc:
        logger.exception("Property analysis task failed for analysis_id=%s", analysis_id)
        db_service.add_analysis_event(
            analysis_id,
            stage="processing_error",
            payload={"error": str(exc)},
        )

        if self.request.retries >= self.max_retries:
            db_service.update_analysis_status(
                analysis_id,
                status="failed",
                error=str(exc),
            )
            return {
                "analysis_id": analysis_id,
                "status": "failed",
                "error": str(exc),
            }

        raise self.retry(exc=exc)
    finally:
        clear_log_context("analysis_id")
