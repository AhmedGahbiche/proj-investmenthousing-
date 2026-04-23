"""
Report-related API endpoints.
Extracted from main app to improve modularity and keep main.py focused.
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from services.database import db_service
from services.report_generator import report_generator
from services.authz import ensure_document_access

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reports"])


def _load_report_generation_inputs(analysis_id: int, request: Request):
    """Load and normalize analysis artifacts needed by all report endpoints."""
    analysis = db_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    output = db_service.get_analysis_output(analysis_id)
    if not output:
        raise HTTPException(status_code=404, detail="Analysis output not found")

    document = db_service.get_document(analysis.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    ensure_document_access(request=request, document=document)

    analysis_dict = {
        "risk_analysis": output.risk_json or {},
        "legal_analysis": output.legal_json or {},
        "valuation_analysis": output.valuation_json or {},
        "final_analysis": output.final_json or {},
        "material_concerns": [],
    }
    metadata = {
        "date": analysis.finished_at.isoformat() if analysis.finished_at else None,
        "analysis_id": analysis_id,
        "document_id": analysis.document_id,
        "filename": document.filename,
    }
    property_id = document.property_id or str(analysis.document_id)

    return analysis, analysis_dict, metadata, property_id


@router.post("/reports/{analysis_id}")
async def create_report(
    request: Request,
    analysis_id: int,
    include_pdf: bool = True,
    save_html: bool = True,
):
    """Generate complete analysis report from existing analysis."""
    try:
        _, analysis_dict, metadata, property_id = _load_report_generation_inputs(analysis_id, request)

        logger.info("Generating report for analysis %s", analysis_id)
        report = report_generator.generate_report(
            property_id=property_id,
            analysis_data=analysis_dict,
            include_pdf=include_pdf,
            save_html=save_html,
            metadata=metadata,
        )

        return {
            "report_id": report.report_id,
            "property_id": report.property_id,
            "status": report.status,
            "generated_at": report.analysis_date,
            "files": {
                "pdf_path": report.pdf_path,
            },
            "error": report.error_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating report: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error creating report")


@router.get("/reports/{analysis_id}/html")
async def get_report_html(analysis_id: int, request: Request):
    """Generate and return analysis report as HTML."""
    try:
        _, analysis_dict, metadata, property_id = _load_report_generation_inputs(analysis_id, request)
        report = report_generator.generate_report(
            property_id=property_id,
            analysis_data=analysis_dict,
            include_pdf=False,
            save_html=True,
            metadata=metadata,
        )

        if not report.status.startswith("completed") or not report.html_path:
            raise HTTPException(status_code=500, detail="Failed to generate HTML report")

        html_path = Path(report.html_path)
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML report file not found")

        return HTMLResponse(content=html_path.read_text(encoding="utf-8"), status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating HTML report: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error generating HTML report")


@router.get("/reports/{analysis_id}/txt")
async def get_report_text(analysis_id: int, request: Request):
    """Return analysis report as plain text."""
    try:
        analysis, analysis_dict, metadata, property_id = _load_report_generation_inputs(analysis_id, request)

        final_analysis = analysis_dict.get("final_analysis", {})
        legal_analysis = analysis_dict.get("legal_analysis", {})
        risk_analysis = analysis_dict.get("risk_analysis", {})
        valuation_analysis = analysis_dict.get("valuation_analysis", {})

        text_lines = [
            "PROPERTY DUE DILIGENCE REPORT",
            "=" * 40,
            f"Analysis ID: {analysis_id}",
            f"Property ID: {property_id}",
            f"Status: {analysis.status}",
            f"Generated At: {metadata.get('date')}",
            "",
            "FINAL ASSESSMENT",
            "-" * 40,
            json.dumps(final_analysis, ensure_ascii=True, indent=2),
            "",
            "LEGAL ANALYSIS",
            "-" * 40,
            json.dumps(legal_analysis, ensure_ascii=True, indent=2),
            "",
            "RISK ANALYSIS",
            "-" * 40,
            json.dumps(risk_analysis, ensure_ascii=True, indent=2),
            "",
            "VALUATION ANALYSIS",
            "-" * 40,
            json.dumps(valuation_analysis, ensure_ascii=True, indent=2),
        ]

        return PlainTextResponse(content="\n".join(text_lines), status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating text report: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error generating text report")


@router.get("/reports/{analysis_id}/pdf")
async def get_report_pdf(analysis_id: int, request: Request):
    """Generate and return analysis report as PDF."""
    try:
        _, analysis_dict, metadata, property_id = _load_report_generation_inputs(analysis_id, request)
        report = report_generator.generate_report(
            property_id=property_id,
            analysis_data=analysis_dict,
            include_pdf=True,
            save_html=False,
            metadata=metadata,
        )

        if not report.status.startswith("completed") or not report.pdf_path:
            raise HTTPException(status_code=500, detail="Failed to generate PDF report")

        pdf_path = Path(report.pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF report file not found")

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"analysis_{analysis_id}.pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating PDF report: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error generating PDF report")


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get report metadata and status."""
    try:
        report_meta = report_generator.get_report(report_id)
        if not report_meta:
            raise HTTPException(status_code=404, detail="Report not found")

        return report_meta
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting report: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error getting report")


@router.get("/reports")
async def list_reports(limit: int = 10):
    """List generated reports."""
    try:
        reports = report_generator.list_reports()
        return {
            "total": len(reports),
            "reports": reports[:limit],
        }
    except Exception as e:
        logger.error("Error listing reports: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error listing reports")
