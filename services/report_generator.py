"""
Simple report generation service for analysis outputs.
Generates HTML and optional PDF artifacts, plus metadata indexing.
"""
import json
import uuid
import html
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class ReportResult:
    report_id: str
    property_id: str
    status: str
    analysis_date: str
    pdf_path: Optional[str] = None
    html_path: Optional[str] = None
    error_message: Optional[str] = None


class ReportGenerator:
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.output_dir / "index.json"

    def _load_index(self) -> List[Dict]:
        if not self.index_file.exists():
            return []
        try:
            return json.loads(self.index_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_index(self, records: List[Dict]) -> None:
        self.index_file.write_text(json.dumps(records, ensure_ascii=True, indent=2), encoding="utf-8")

    def _render_html(self, property_id: str, analysis_data: Dict, metadata: Dict) -> str:
        legal = analysis_data.get("legal_analysis", {})
        risk = analysis_data.get("risk_analysis", {})
        valuation = analysis_data.get("valuation_analysis", {})
        final = analysis_data.get("final_analysis", {})

        safe_property_id = html.escape(str(property_id))
        safe_generated_at = html.escape(datetime.utcnow().isoformat())
        safe_final = html.escape(json.dumps(final, ensure_ascii=True, indent=2))
        safe_legal = html.escape(json.dumps(legal, ensure_ascii=True, indent=2))
        safe_risk = html.escape(json.dumps(risk, ensure_ascii=True, indent=2))
        safe_valuation = html.escape(json.dumps(valuation, ensure_ascii=True, indent=2))
        safe_metadata = html.escape(json.dumps(metadata, ensure_ascii=True, indent=2))

        return f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
    <title>Due Diligence Report - {safe_property_id}</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 30px; color: #0f172a; }}
    h1, h2 {{ margin-bottom: 6px; }}
    .card {{ border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin: 14px 0; }}
    .meta {{ color: #475569; font-size: 13px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; padding: 10px; border-radius: 8px; }}
  </style>
</head>
<body>
  <h1>Property Due Diligence Report</h1>
    <div class=\"meta\">Property ID: {safe_property_id} | Generated: {safe_generated_at}</div>

  <div class=\"card\">
    <h2>Final Assessment</h2>
        <pre>{safe_final}</pre>
  </div>

  <div class=\"card\">
    <h2>Legal Analysis</h2>
        <pre>{safe_legal}</pre>
  </div>

  <div class=\"card\">
    <h2>Risk Analysis</h2>
        <pre>{safe_risk}</pre>
  </div>

  <div class=\"card\">
    <h2>Valuation Analysis</h2>
        <pre>{safe_valuation}</pre>
  </div>

  <div class=\"card\">
    <h2>Metadata</h2>
        <pre>{safe_metadata}</pre>
  </div>
</body>
</html>
"""

    def generate_report(
        self,
        property_id: str,
        analysis_data: Dict,
        include_pdf: bool = True,
        save_html: bool = True,
        metadata: Optional[Dict] = None,
    ) -> ReportResult:
        report_id = str(uuid.uuid4())
        metadata = metadata or {}

        html_path = None
        pdf_path = None
        pdf_error = None

        try:
            html_content = self._render_html(property_id, analysis_data, metadata)

            if save_html:
                html_file = self.output_dir / f"{report_id}.html"
                html_file.write_text(html_content, encoding="utf-8")
                html_path = str(html_file)

            if include_pdf:
                try:
                    import importlib
                    HTML = importlib.import_module("weasyprint").HTML
                    pdf_file = self.output_dir / f"{report_id}.pdf"
                    HTML(string=html_content).write_pdf(str(pdf_file))
                    pdf_path = str(pdf_file)
                except Exception as pdf_exc:
                    logger.warning("PDF generation failed for report %s: %s", report_id, str(pdf_exc))
                    pdf_path = None
                    pdf_error = str(pdf_exc)

            status = "completed_with_warnings" if include_pdf and pdf_path is None else "completed"
            error_message = "PDF generation failed" if pdf_error else None

            result = ReportResult(
                report_id=report_id,
                property_id=property_id,
                status=status,
                analysis_date=datetime.utcnow().isoformat(),
                pdf_path=pdf_path,
                html_path=html_path,
                error_message=error_message,
            )

            records = self._load_index()
            records.insert(0, {
                "report_id": result.report_id,
                "property_id": result.property_id,
                "status": result.status,
                "analysis_date": result.analysis_date,
                "pdf_path": result.pdf_path,
                "html_path": result.html_path,
                "metadata": metadata,
            })
            self._save_index(records)
            return result

        except Exception as e:
            logger.error("Report generation failed for property_id=%s: %s", property_id, str(e), exc_info=True)
            return ReportResult(
                report_id=report_id,
                property_id=property_id,
                status="failed",
                analysis_date=datetime.utcnow().isoformat(),
                error_message="Report generation failed",
            )

    def get_report(self, report_id: str) -> Optional[Dict]:
        records = self._load_index()
        for record in records:
            if record.get("report_id") == report_id:
                return record
        return None

    def list_reports(self) -> List[Dict]:
        return self._load_index()


report_generator = ReportGenerator()
