"""
Asynchronous analysis tasks.
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from celery_app import celery_app
from services.database import db_service
from services.regulation_retrieval import regulation_retrieval_service
from services.analysis_intelligence import analysis_intelligence_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_analysis_task(self, document_id: int, analysis_id: int):
    """
    Run document analysis asynchronously with retries and status tracking.
    """
    try:
        db_service.update_analysis_status(analysis_id, status="processing")
        db_service.add_analysis_event(analysis_id, stage="processing_started")

        extracted_text = db_service.get_document_text(document_id)
        if not extracted_text or not extracted_text.raw_text.strip():
            raise ValueError("No extracted text available for analysis")

        document_text = extracted_text.raw_text
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

            legal_json = legal_future.result()
            risk_json = risk_future.result()
            valuation_json = valuation_future.result()

        db_service.add_analysis_event(analysis_id, stage="final_synthesis_started")
        final_json = analysis_intelligence_service.final_due_diligence(
            document_text=document_text,
            contexts=contexts,
            legal_json=legal_json,
            risk_json=risk_json,
            valuation_json=valuation_json,
        )

        db_service.save_analysis_output(
            analysis_id=analysis_id,
            legal_json=legal_json,
            risk_json=risk_json,
            valuation_json=valuation_json,
            final_json=final_json,
        )
        db_service.add_analysis_event(analysis_id, stage="outputs_saved")

        db_service.update_analysis_status(analysis_id, status="done")
        db_service.add_analysis_event(analysis_id, stage="processing_done")

        return {
            "analysis_id": analysis_id,
            "status": "done",
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
