"""
Mock backend server for frontend development and testing.
Provides a lightweight FastAPI server that mimics the real backend API
without requiring PostgreSQL, Redis, or heavy ML dependencies.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os
import requests
import io
import textwrap
import html
import time
from pathlib import Path
from dotenv import load_dotenv

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

# ============================================================================
# API Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "90"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

LAST_OPENAI_ERROR = ""

# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="Document Analysis API (Mock)",
    version="1.0.0",
    description="Mock backend for document management system"
)

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class UploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
    error: Optional[str] = None


class Document(BaseModel):
    id: int
    filename: str
    file_format: str
    file_size: int
    upload_timestamp: str
    document_type: Optional[str] = None
    property_id: Optional[str] = None


class ExtractedText(BaseModel):
    id: int
    document_id: int
    raw_text: str
    extraction_timestamp: str
    extraction_status: str = "success"  # "success" | "failed" | "partial"
    extraction_error: Optional[str] = None


class SearchResult(BaseModel):
    document_id: int
    filename: str
    similarity_score: float
    excerpt: str


class HealthCheck(BaseModel):
    status: str
    timestamp: str


class SystemStatus(BaseModel):
    status: str
    database: str
    cache: str
    message_queue: str
    timestamp: str


class AnalysisOutput(BaseModel):
    legal_json: Optional[dict] = None
    risk_json: Optional[dict] = None
    valuation_json: Optional[dict] = None
    final_json: Optional[dict] = None


class AnalysisCreateResponse(BaseModel):
    success: bool
    analysis_id: int
    document_id: int
    status: str
    task_id: Optional[str] = None


class AnalyzePropertyRequest(BaseModel):
    document_ids: List[int]
    property_name: Optional[str] = None


class AnalysisPropertyCreateResponse(BaseModel):
    success: bool
    analysis_id: int
    document_ids: List[int]
    status: str
    report_url: str


class AnalysisStatus(BaseModel):
    analysis_id: int
    document_id: int
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    model_version: Optional[str] = None
    outputs: Optional[AnalysisOutput] = None


# ============================================================================
# Global Storage (In-Memory)
# ============================================================================

documents_db = {}
extracted_texts_db = {}
analysis_db = {}  # Store analysis results
next_document_id = 1
next_analysis_id = 1
uploads_dir = Path("./mock_uploads")
uploads_dir.mkdir(exist_ok=True)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@app.get("/system/status")
async def system_status():
    """Get system status"""
    return SystemStatus(
        status="operational",
        database="mock (in-memory)",
        cache="mock (in-memory)",
        message_queue="mock (in-memory)",
        timestamp=datetime.now().isoformat()
    )


# ============================================================================
# Document Upload Endpoint
# ============================================================================

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document file"""
    global next_document_id
    
    try:
        # Validate file type
        allowed_types = {".pdf", ".docx", ".png", ".txt"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if file_size > 50 * 1024 * 1024:  # 50 MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 50 MB limit")
        
        # Save file
        file_path = uploads_dir / f"{next_document_id}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create document record
        doc_id = next_document_id
        next_document_id += 1
        
        # Extract file extension without dot
        file_format = file_ext.lstrip('.')
        
        doc = {
            "id": doc_id,
            "filename": file.filename,
            "file_format": file_format,
            "file_size": file_size,
            "upload_timestamp": datetime.now().isoformat(),
            "document_type": None,
            "property_id": None,
            "file_path": str(file_path)
        }
        
        documents_db[doc_id] = doc
        
        # Mock: Simulate text extraction
        mock_text = f"Extracted text from {file.filename}. This is a mock extraction for demonstration purposes."
        extracted_texts_db[doc_id] = {
            "id": doc_id,
            "document_id": doc_id,
            "raw_text": mock_text,
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_status": "success",
            "extraction_error": None
        }
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded {file.filename}",
            document_id=doc_id,
            filename=file.filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return UploadResponse(
            success=False,
            message="Upload failed",
            error=str(e)
        )


# ============================================================================
# Document Retrieval Endpoints
# ============================================================================

@app.get("/documents")
async def list_documents(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """List all uploaded documents"""
    docs = list(documents_db.values())
    return docs[skip:skip + limit]


@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    """Get document details"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return documents_db[document_id]


@app.get("/documents/{document_id}/text")
async def get_extracted_text(document_id: int):
    """Get extracted text from a document"""
    if document_id not in extracted_texts_db:
        raise HTTPException(status_code=404, detail="Text not found")
    
    return extracted_texts_db[document_id]


class DocumentWithTextResponse(BaseModel):
    document: Document
    extracted_text: Optional[ExtractedText] = None


@app.get("/documents/{document_id}/full")
async def get_full_document(document_id: int):
    """Get full document with extracted text"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = documents_db[document_id]
    extracted_text = extracted_texts_db.get(document_id)
    
    return DocumentWithTextResponse(
        document=Document(**doc_data),
        extracted_text=ExtractedText(**extracted_text) if extracted_text else None
    )


# ============================================================================
# Search Endpoint
# ============================================================================

@app.post("/search/semantic")
async def semantic_search(query: str = Query(...)):
    """Perform semantic search across documents"""
    results = []
    
    # Mock search: simple keyword matching
    query_lower = query.lower()
    for doc_id, doc in documents_db.items():
        if query_lower in doc["filename"].lower():
            results.append(SearchResult(
                document_id=doc_id,
                filename=doc["filename"],
                similarity_score=0.85,
                excerpt=f"Found in {doc['filename']}"
            ))
    
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }


@app.post("/documents/{document_id}/search")
async def search_document(document_id: int, query: str = Query(...)):
    """Search within a specific document"""
    if document_id not in extracted_texts_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    text = extracted_texts_db[document_id]["raw_text"]
    query_lower = query.lower()
    
    if query_lower in text.lower():
        return {
            "document_id": document_id,
            "query": query,
            "found": True,
            "matches": 1
        }
    
    return {
        "document_id": document_id,
        "query": query,
        "found": False,
        "matches": 0
    }


# ============================================================================
# Analysis Endpoints
# ============================================================================

class AnalyzeRequest(BaseModel):
    document_id: int
    model_version: Optional[str] = None


def _build_analysis_prompt(text: str) -> str:
    doc_text = text[:2000] if text else "No text available"
    return f"""You are an expert real-estate due diligence analyst. Analyze the following document text and provide:

1. A legal analysis in JSON format with keys: risk_level (low/medium/high), summary, flags (array of issues)
2. A risk analysis in JSON format with keys: overall_risk_score (0-10), risk_level, identified_risks (array with type, description, severity)
3. A valuation analysis in JSON format with keys: estimated_value (number), confidence_score (0-1), valuation_method
4. A final recommendation JSON with keys: overall_recommendation, decision

Document text:
{doc_text}

Respond with valid JSON containing exactly these four keys: "legal_json", "risk_json", "valuation_json", "final_json" """


def _extract_json_payload(content: str) -> dict | None:
    try:
        if "```json" in content:
            content = content.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in content:
            content = content.split("```", 1)[1].split("```", 1)[0]
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
        return None
    except Exception:
        return None


def analyze_with_openai(text: str) -> dict | None:
    """Call OpenAI API to analyze document text."""
    global LAST_OPENAI_ERROR

    if not OPENAI_API_KEY:
        LAST_OPENAI_ERROR = "OPENAI_API_KEY is missing"
        return None

    try:
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You output strict JSON only.",
                },
                {
                    "role": "user",
                    "content": _build_analysis_prompt(text),
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        for attempt in range(OPENAI_MAX_RETRIES + 1):
            try:
                response = requests.post(
                    OPENAI_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=OPENAI_TIMEOUT_SECONDS,
                )
                if response.status_code != 200:
                    LAST_OPENAI_ERROR = f"HTTP {response.status_code}: {response.text[:500]}"
                    print(f"OpenAI API error: {LAST_OPENAI_ERROR}")
                    return None
                break
            except requests.exceptions.Timeout:
                LAST_OPENAI_ERROR = (
                    f"Timeout after {OPENAI_TIMEOUT_SECONDS}s (attempt {attempt + 1}/{OPENAI_MAX_RETRIES + 1})"
                )
                print(f"OpenAI call timeout: {LAST_OPENAI_ERROR}")
                if attempt >= OPENAI_MAX_RETRIES:
                    return None
                time.sleep(1.5 * (attempt + 1))
            except requests.exceptions.ConnectionError as e:
                LAST_OPENAI_ERROR = f"Connection error: {e}"
                print(f"OpenAI call connection error: {LAST_OPENAI_ERROR}")
                if attempt >= OPENAI_MAX_RETRIES:
                    return None
                time.sleep(1.0 * (attempt + 1))

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "{}")
        )
        parsed = _extract_json_payload(content)
        if parsed is None:
            print("OpenAI response parsing failed")
            LAST_OPENAI_ERROR = "OpenAI response parsing failed (non-JSON output)"
            return None
        LAST_OPENAI_ERROR = ""
        return parsed
    except Exception as e:
        LAST_OPENAI_ERROR = str(e)
        print(f"OpenAI call failed: {e}")
        return None


def get_mock_analysis() -> dict:
    """Return mock analysis when API fails"""
    return {
        "legal_json": {
            "risk_level": "low",
            "summary": "Standard document with market-rate provisions.",
            "flags": []
        },
        "risk_json": {
            "overall_risk_score": 2.5,
            "risk_level": "low",
            "identified_risks": [
                {
                    "type": "standard",
                    "description": "Standard market terms",
                    "severity": "low"
                }
            ]
        },
        "valuation_json": {
            "estimated_value": 0,
            "confidence_score": 0.0,
            "valuation_method": "mock"
        },
        "final_json": {
            "overall_recommendation": "Proceed with standard due diligence follow-up.",
            "decision": "conditional_go"
        }
    }


def analyze_with_llm(text: str) -> tuple[dict | None, str | None]:
    """OpenAI-only analysis. Return analysis and source label."""
    openai_result = analyze_with_openai(text)
    if openai_result is not None:
        return openai_result, "openai"
    return None, None


def _build_report_html(analysis_id: int, analysis: dict) -> str:
    outputs = analysis.get("outputs", {}) or {}
    legal = outputs.get("legal_json", {})
    risk = outputs.get("risk_json", {})
    valuation = outputs.get("valuation_json", {})
    final = outputs.get("final_json", {})

    final_text = html.escape("\n".join(_to_report_lines(final)))
    legal_text = html.escape("\n".join(_to_report_lines(legal)))
    risk_text = html.escape("\n".join(_to_report_lines(risk)))
    valuation_text = html.escape("\n".join(_to_report_lines(valuation)))
    status = html.escape(str(analysis.get("status", "unknown")))
    generated_at = html.escape(datetime.now().isoformat())
    llm_source = html.escape(str(final.get("llm_source", "unknown")))

    risk_level = str(risk.get("risk_level", "unknown")).lower()
    if risk_level == "high":
        risk_class = "chip-high"
    elif risk_level == "medium":
        risk_class = "chip-medium"
    else:
        risk_class = "chip-low"

    return f"""
<!doctype html>
<html>
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Property Analysis Report #{analysis_id}</title>
    <style>
        :root {{
            --bg: #f2f6fa;
            --ink: #112031;
            --muted: #4d6075;
            --line: #d9e3ee;
            --surface: #ffffff;
            --brand: #0f4b65;
            --brand-2: #1f6788;
            --ok: #1f8a5a;
            --warn: #b7801d;
            --bad: #b84141;
            --shadow: 0 14px 34px rgba(15, 32, 49, 0.08);
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: "Segoe UI", Tahoma, Arial, sans-serif;
            color: var(--ink);
            background: radial-gradient(circle at 90% 0%, #e3f0f8 0, transparent 36%), var(--bg);
        }}
        .shell {{ width: min(1080px, 92vw); margin: 26px auto 34px; }}
        .hero {{
            background: linear-gradient(140deg, var(--brand), var(--brand-2));
            color: #fff;
            border-radius: 16px;
            padding: 22px 24px;
            box-shadow: var(--shadow);
        }}
        .hero h1 {{ margin: 0 0 8px; font-size: 32px; }}
        .hero p {{ margin: 0; opacity: 0.95; }}
        .meta-grid {{
            margin-top: 14px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        .meta {{
            background: rgba(255, 255, 255, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.26);
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 14px;
        }}
        .muted {{ opacity: 0.86; font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; }}
        .value {{ font-weight: 700; margin-top: 4px; }}
        .content {{ margin-top: 16px; display: grid; gap: 12px; }}
        .card {{
            border: 1px solid var(--line);
            border-radius: 14px;
            background: var(--surface);
            box-shadow: var(--shadow);
            overflow: hidden;
        }}
        .card-head {{
            padding: 12px 14px;
            border-bottom: 1px solid var(--line);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8fbfe;
        }}
        .card-head h2 {{ margin: 0; font-size: 16px; }}
        .chip {{
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 700;
            border: 1px solid transparent;
        }}
        .chip-low {{ color: var(--ok); background: #eaf8f1; border-color: #c9ecd9; }}
        .chip-medium {{ color: var(--warn); background: #fff5e6; border-color: #ffe0aa; }}
        .chip-high {{ color: var(--bad); background: #fff0f0; border-color: #ffcfcf; }}
        .card-body {{ padding: 14px; }}
        pre {{
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: Consolas, "Courier New", monospace;
            font-size: 13px;
            line-height: 1.5;
            color: #1b2c3e;
            background: #f6f9fc;
            border: 1px solid #e1e9f1;
            border-radius: 10px;
            padding: 12px;
        }}
        .footer {{
            margin-top: 14px;
            color: var(--muted);
            font-size: 12px;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class=\"shell\">
        <section class=\"hero\">
            <h1>Property Due Diligence Report</h1>
            <p>Comprehensive legal, risk, and valuation assessment generated from the uploaded property dossier.</p>
            <div class=\"meta-grid\">
                <div class=\"meta\"><div class=\"muted\">Analysis ID</div><div class=\"value\">{analysis_id}</div></div>
                <div class=\"meta\"><div class=\"muted\">Status</div><div class=\"value\">{status}</div></div>
                <div class=\"meta\"><div class=\"muted\">LLM Source</div><div class=\"value\">{llm_source}</div></div>
                <div class=\"meta\"><div class=\"muted\">Generated At</div><div class=\"value\">{generated_at}</div></div>
            </div>
        </section>

        <section class=\"content\">
            <article class=\"card\">
                <div class=\"card-head\"><h2>Final Recommendation</h2></div>
                <div class=\"card-body\"><pre>{final_text}</pre></div>
            </article>

            <article class=\"card\">
                <div class=\"card-head\"><h2>Legal Analysis</h2></div>
                <div class=\"card-body\"><pre>{legal_text}</pre></div>
            </article>

            <article class=\"card\">
                <div class=\"card-head\"><h2>Risk Analysis</h2><span class=\"chip {risk_class}\">{risk_level.upper()}</span></div>
                <div class=\"card-body\"><pre>{risk_text}</pre></div>
            </article>

            <article class=\"card\">
                <div class=\"card-head\"><h2>Valuation Analysis</h2></div>
                <div class=\"card-body\"><pre>{valuation_text}</pre></div>
            </article>
        </section>

        <div class=\"footer\">Generated by Taqim Analysis Engine</div>
    </div>
</body>
</html>
"""


def _format_key(key: str) -> str:
    return key.replace("_", " ").strip().capitalize()


def _to_report_lines(value, prefix: str = "") -> List[str]:
    if isinstance(value, dict):
        lines: List[str] = []
        for k, v in value.items():
            label = _format_key(str(k))
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{label}:")
                lines.extend(_to_report_lines(v, prefix + "  "))
            else:
                lines.append(f"{prefix}{label}: {v}")
        return lines or [f"{prefix}No data"]

    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_to_report_lines(item, prefix + "  "))
            else:
                lines.append(f"{prefix}- {item}")
        return lines or [f"{prefix}No items"]

    return [f"{prefix}{value}"]


def _build_report_text(analysis_id: int, analysis: dict) -> str:
    outputs = analysis.get("outputs", {}) or {}
    legal = outputs.get("legal_json", {})
    risk = outputs.get("risk_json", {})
    valuation = outputs.get("valuation_json", {})
    final = outputs.get("final_json", {})

    lines = [
        "PROPERTY DUE DILIGENCE REPORT",
        "=" * 40,
        f"Analysis ID: {analysis_id}",
        f"Status: {analysis.get('status', 'unknown')}",
        f"Generated At: {datetime.now().isoformat()}",
        "",
        "FINAL RECOMMENDATION",
        "-" * 40,
        *_to_report_lines(final),
        "",
        "LEGAL ANALYSIS",
        "-" * 40,
        *_to_report_lines(legal),
        "",
        "RISK ANALYSIS",
        "-" * 40,
        *_to_report_lines(risk),
        "",
        "VALUATION ANALYSIS",
        "-" * 40,
        *_to_report_lines(valuation),
    ]
    return "\n".join(lines)


def _build_report_pdf_bytes(analysis_id: int, analysis: dict) -> bytes:
    outputs = analysis.get("outputs", {}) or {}
    legal = outputs.get("legal_json", {}) or {}
    risk = outputs.get("risk_json", {}) or {}
    valuation = outputs.get("valuation_json", {}) or {}
    final = outputs.get("final_json", {}) or {}

    def _score(value: object, default: int) -> int:
        if isinstance(value, (int, float)):
            return max(0, min(100, int(value)))
        if isinstance(value, str):
            try:
                return max(0, min(100, int(float(value))))
            except ValueError:
                return default
        return default

    def _score_badge(score_value: int) -> tuple[str, colors.Color]:
        if score_value >= 85:
            return "Excellent", colors.HexColor("#0F9D58")
        if score_value >= 70:
            return "Stable", colors.HexColor("#F4B400")
        return "Attention", colors.HexColor("#DB4437")

    def _draw_wrapped_text(
        c: canvas.Canvas,
        text_value: str,
        x: float,
        y: float,
        width_limit: float,
        font_name: str = "Helvetica",
        font_size: int = 10,
        leading: float = 14,
        color: colors.Color = colors.black,
    ) -> float:
        c.setFont(font_name, font_size)
        c.setFillColor(color)
        words = (text_value or "").split()
        if not words:
            return y

        line = words[0]
        current_y = y
        for word in words[1:]:
            candidate = f"{line} {word}"
            if pdfmetrics.stringWidth(candidate, font_name, font_size) <= width_limit:
                line = candidate
            else:
                c.drawString(x, current_y, line)
                current_y -= leading
                line = word
        c.drawString(x, current_y, line)
        return current_y - leading

    def _render_section(
        c: canvas.Canvas,
        title: str,
        score_value: int,
        summary_value: str,
        details: list[str],
        y_start: float,
        page_width: float,
        page_height: float,
        margin: float,
    ) -> float:
        section_top = y_start
        card_width = page_width - (2 * margin)
        min_height = 110

        if section_top < (margin + min_height):
            c.showPage()
            section_top = page_height - margin

        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#DCE3EE"))
        c.roundRect(margin, section_top - min_height, card_width, min_height, 8, fill=1, stroke=1)

        c.setFillColor(colors.HexColor("#0A2A5E"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin + 14, section_top - 24, title)

        badge_text, badge_color = _score_badge(score_value)
        c.setFillColor(badge_color)
        c.roundRect(margin + card_width - 130, section_top - 34, 114, 20, 10, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(margin + card_width - 73, section_top - 21, f"{badge_text} | {score_value}/100")

        y_cursor = _draw_wrapped_text(
            c,
            summary_value or "No summary available.",
            margin + 14,
            section_top - 48,
            card_width - 28,
            font_name="Helvetica",
            font_size=10,
            leading=13,
            color=colors.HexColor("#3F4A5A"),
        )

        y_cursor -= 4
        c.setFillColor(colors.HexColor("#5A6678"))
        c.setFont("Helvetica", 9)
        max_detail_lines = 2
        for line in details[:max_detail_lines]:
            short_line = line[:120]
            c.drawString(margin + 14, y_cursor, f"- {short_line}")
            y_cursor -= 12

        return section_top - min_height - 14

    legal_score = _score(legal.get("score") or legal.get("confidence"), 90)
    risk_score = _score(risk.get("score") or risk.get("confidence"), 84)
    valuation_score = _score(valuation.get("score") or valuation.get("confidence"), 88)

    overall_recommendation = str(
        final.get("recommendation")
        or final.get("summary")
        or final.get("executive_summary")
        or "This property appears suitable for due diligence continuation based on current indicators."
    )
    risk_level = str(final.get("risk_level") or final.get("overall_risk") or "Moderate")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    margin_x = 36
    content_width = width - (2 * margin_x)

    # Corporate header band
    c.setFillColor(colors.HexColor("#0A2A5E"))
    c.rect(0, height - 120, width, 120, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin_x, height - 52, "TAQIM AUTHORITY")
    c.setFont("Helvetica", 10)
    c.drawString(margin_x, height - 70, "Property Due Diligence Report")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - margin_x, height - 52, f"Report #{analysis_id}")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin_x, height - 69, f"Generated {generated_at}")

    # Meta strip
    c.setFillColor(colors.HexColor("#F2F5FA"))
    c.roundRect(margin_x, height - 162, content_width, 28, 6, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#2D3A4D"))
    c.setFont("Helvetica", 9)
    c.drawString(margin_x + 10, height - 145, f"Status: {analysis.get('status', 'unknown').upper()}")
    c.drawString(margin_x + 170, height - 145, f"Risk Level: {risk_level}")
    c.drawRightString(width - margin_x - 10, height - 145, "Confidential - Internal Distribution")

    # Recommendation block
    rec_top = height - 182
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#DCE3EE"))
    c.roundRect(margin_x, rec_top - 92, content_width, 92, 8, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#0A2A5E"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x + 14, rec_top - 22, "Executive Recommendation")
    _draw_wrapped_text(
        c,
        overall_recommendation,
        margin_x + 14,
        rec_top - 40,
        content_width - 28,
        font_name="Helvetica",
        font_size=10,
        leading=13,
        color=colors.HexColor("#3F4A5A"),
    )

    y = rec_top - 106

    # Score summary cards
    gap = 10
    box_w = (content_width - (2 * gap)) / 3
    score_data = [
        ("Legal Compliance", legal_score, str(legal.get("summary") or legal.get("status") or "Legal checks completed.")),
        ("Risk Assessment", risk_score, str(risk.get("summary") or risk.get("status") or "Risk profile generated.")),
        ("Valuation", valuation_score, str(valuation.get("summary") or valuation.get("status") or "Valuation benchmark completed.")),
    ]

    for idx, (label, score_value, desc) in enumerate(score_data):
        x = margin_x + (idx * (box_w + gap))
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#DCE3EE"))
        c.roundRect(x, y - 94, box_w, 94, 8, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#5A6678"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 10, y - 18, label.upper())
        c.setFillColor(colors.HexColor("#0A2A5E"))
        c.setFont("Helvetica-Bold", 22)
        c.drawString(x + 10, y - 48, f"{score_value}")
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#5A6678"))
        c.drawString(x + 45, y - 45, "/ 100")
        c.setFont("Helvetica", 8)
        snippet = textwrap.shorten(desc, width=48, placeholder="...")
        c.drawString(x + 10, y - 69, snippet)

    y -= 112

    # Detailed sections
    y = _render_section(
        c,
        "Legal Analysis",
        legal_score,
        str(legal.get("summary") or legal.get("status") or "No legal summary available."),
        _to_report_lines(legal),
        y,
        width,
        height,
        margin_x,
    )
    y = _render_section(
        c,
        "Risk Analysis",
        risk_score,
        str(risk.get("summary") or risk.get("status") or "No risk summary available."),
        _to_report_lines(risk),
        y,
        width,
        height,
        margin_x,
    )
    y = _render_section(
        c,
        "Valuation Analysis",
        valuation_score,
        str(valuation.get("summary") or valuation.get("status") or "No valuation summary available."),
        _to_report_lines(valuation),
        y,
        width,
        height,
        margin_x,
    )

    # Footer
    c.setFillColor(colors.HexColor("#7A889D"))
    c.setFont("Helvetica", 8)
    c.drawString(margin_x, 24, "Taqim Real Estate Solutions - Certified Due Diligence Document")
    c.drawRightString(width - margin_x, 24, f"Analysis ID: {analysis_id}")

    c.save()
    packet.seek(0)
    return packet.read()

@app.post("/analyze")
async def create_analysis(request: AnalyzeRequest):
    """Create analysis for a document"""
    global next_analysis_id
    
    document_id = request.document_id
    
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get extracted text
    extracted_text = extracted_texts_db.get(document_id)
    if not extracted_text:
        raise HTTPException(status_code=404, detail="No extracted text found")
    
    # Call LLM API (OpenAI first, Claude fallback) to analyze the text
    text_to_analyze = extracted_text.get("raw_text", "")
    analysis_results, llm_source = analyze_with_llm(text_to_analyze)
    
    if analysis_results is None:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI analysis failed. No fallback is enabled. Reason: {LAST_OPENAI_ERROR or 'unknown error'}",
        )
    
    # Create analysis record
    analysis_id = next_analysis_id
    next_analysis_id += 1
    
    analysis = {
        "analysis_id": analysis_id,
        "document_id": document_id,
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "finished_at": datetime.now().isoformat(),
        "outputs": {
            "legal_json": analysis_results.get("legal_json", {}),
            "risk_json": analysis_results.get("risk_json", {}),
            "valuation_json": analysis_results.get("valuation_json", {}),
            "final_json": {
                **analysis_results.get("final_json", {}),
                "analysis_id": analysis_id,
                "report_url": f"/reports/{analysis_id}/html",
                "llm_source": llm_source,
            }
        }
    }
    
    analysis_db[analysis_id] = analysis
    
    return AnalysisCreateResponse(
        success=True,
        analysis_id=analysis_id,
        document_id=document_id,
        status="completed"
    )


@app.post("/analyze/property")
async def create_property_analysis(request: AnalyzePropertyRequest):
    """Create one combined analysis for all documents belonging to a single property."""
    global next_analysis_id

    if not request.document_ids:
        raise HTTPException(status_code=400, detail="document_ids is required")

    missing_ids = [doc_id for doc_id in request.document_ids if doc_id not in documents_db]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Documents not found: {missing_ids}")

    combined_text_parts = []
    for doc_id in request.document_ids:
        extracted_text = extracted_texts_db.get(doc_id)
        if extracted_text and extracted_text.get("raw_text"):
            filename = documents_db[doc_id]["filename"]
            combined_text_parts.append(f"[{filename}]\n{extracted_text['raw_text']}")

    if not combined_text_parts:
        raise HTTPException(status_code=404, detail="No extracted text found for the provided documents")

    combined_text = "\n\n".join(combined_text_parts)
    analysis_results, llm_source = analyze_with_llm(combined_text)
    if analysis_results is None:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI analysis failed. No fallback is enabled. Reason: {LAST_OPENAI_ERROR or 'unknown error'}",
        )

    analysis_id = next_analysis_id
    next_analysis_id += 1

    primary_document_id = request.document_ids[0]
    analysis = {
        "analysis_id": analysis_id,
        "document_id": primary_document_id,
        "document_ids": request.document_ids,
        "property_name": request.property_name,
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "finished_at": datetime.now().isoformat(),
        "outputs": {
            "legal_json": analysis_results.get("legal_json", {}),
            "risk_json": analysis_results.get("risk_json", {}),
            "valuation_json": analysis_results.get("valuation_json", {}),
            "final_json": {
                **analysis_results.get("final_json", {}),
                "analysis_id": analysis_id,
                "report_url": f"/reports/{analysis_id}/html",
                "documents_analyzed": request.document_ids,
                "llm_source": llm_source,
            },
        },
    }
    analysis_db[analysis_id] = analysis

    return AnalysisPropertyCreateResponse(
        success=True,
        analysis_id=analysis_id,
        document_ids=request.document_ids,
        status="completed",
        report_url=f"/reports/{analysis_id}/html",
    )


@app.get("/analyze/{analysis_id}")
async def get_analysis_status(analysis_id: int):
    """Get analysis status"""
    if analysis_id not in analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_db[analysis_id]
    return AnalysisStatus(
        analysis_id=analysis_id,
        document_id=analysis["document_id"],
        status=analysis["status"],
        started_at=analysis.get("started_at"),
        finished_at=analysis.get("finished_at"),
        error=analysis.get("error"),
        model_version="mock-1.0",
        outputs=AnalysisOutput(**analysis["outputs"]) if analysis.get("outputs") else None
    )


@app.get("/reports/{analysis_id}/html")
async def get_analysis_report_html(analysis_id: int):
    """Return a generated HTML report for a completed analysis."""
    if analysis_id not in analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analysis_db[analysis_id]
    html = _build_report_html(analysis_id, analysis)
    return HTMLResponse(content=html, status_code=200)


@app.get("/reports/{analysis_id}/txt")
async def get_analysis_report_text(analysis_id: int):
    """Return a plain-text report for a completed analysis."""
    if analysis_id not in analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analysis_db[analysis_id]
    text_report = _build_report_text(analysis_id, analysis)
    return PlainTextResponse(content=text_report, status_code=200)


@app.get("/reports/{analysis_id}/pdf")
async def get_analysis_report_pdf(analysis_id: int):
    """Return a generated PDF report for a completed analysis."""
    if analysis_id not in analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analysis_db[analysis_id]
    pdf_bytes = _build_report_pdf_bytes(analysis_id, analysis)
    headers = {
        "Content-Disposition": f"inline; filename=property_report_{analysis_id}.pdf"
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@app.get("/diagnostics/analysis/{analysis_id}")
async def get_analysis_diagnostics(analysis_id: int):
    """Diagnostic endpoint to confirm report generation source and pipeline status."""
    if analysis_id not in analysis_db:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analysis_db[analysis_id]
    final_json = (analysis.get("outputs") or {}).get("final_json", {})
    return {
        "analysis_id": analysis_id,
        "status": analysis.get("status"),
        "report_url": final_json.get("report_url", f"/reports/{analysis_id}/html"),
        "llm_source": final_json.get("llm_source", "unknown"),
        "embeddings_enabled": False,
        "embeddings_note": "Mock backend does not run vector embeddings. Use main backend /search endpoints to validate embedding pipeline.",
    }


# ============================================================================
# Startup Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("✓ Mock Backend Server Started")
    print(f"  - API running on: http://localhost:8000")
    print(f"  - Health check: GET /health")
    print(f"  - Swagger UI: GET /docs")
    print(f"  - OpenAI key detected: {'yes' if bool(OPENAI_API_KEY) else 'no'}")
    print(f"  - OpenAI timeout: {OPENAI_TIMEOUT_SECONDS}s, retries: {OPENAI_MAX_RETRIES}")
    print("  - Fallback providers: disabled (OpenAI only)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
