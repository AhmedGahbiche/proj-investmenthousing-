"""
LLM-powered analysis intelligence service for complete due diligence.
"""
import json
import logging
from typing import Dict, List

from openai import OpenAI
from config import settings
from services.analysis_schemas import validate_module_output

logger = logging.getLogger(__name__)


def _safe_json_loads(raw_content: str) -> Dict:
    """Parse JSON safely from model output."""
    if not raw_content:
        return {}

    candidate = raw_content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        logger.warning("Model output was not valid JSON; returning wrapped raw output")
        return {
            "raw_output": raw_content,
            "parsing_error": "invalid_json",
            "score": 0,
            "summary": "Model response could not be parsed as JSON",
        }


class AnalysisIntelligenceService:
    """Calls OpenAI models for legal, risk, valuation, and final due diligence synthesis."""

    SYSTEM_PROMPT = (
        "You are a senior due-diligence analyst specialized in Tunisian real estate. "
        "You evaluate legal validity, construction/material risk, and valuation fairness. "
        "Always return strict JSON with concise, evidence-backed conclusions. "
        "Do not invent facts; if evidence is missing, state uncertainty clearly. "
        "Score from 0 to 100 where 100 means low risk/high confidence."
    )

    def __init__(self):
        self.client = None
        self.model = settings.OPENAI_MODEL

    def _ensure_client(self) -> None:
        if self.client is not None:
            return

        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required for analysis intelligence")

        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL

        self.client = OpenAI(**client_kwargs)

    def _contexts_to_text(self, contexts: List[Dict]) -> str:
        if not contexts:
            return "No regulation context retrieved."

        lines: List[str] = []
        for ctx in contexts:
            lines.append(
                f"- rank={ctx.get('rank')} regulation_id={ctx.get('regulation_id')} "
                f"similarity={ctx.get('similarity_score')}: {ctx.get('text', 'N/A')}"
            )
        return "\n".join(lines)

    def _call_json(self, module_name: str, schema_hint: Dict, document_text: str, contexts: List[Dict]) -> Dict:
        self._ensure_client()
        context_text = self._contexts_to_text(contexts)

        user_prompt = (
            f"Module: {module_name}\n"
            "Task: perform complete due diligence for this module using document evidence and context.\n"
            "Return ONLY valid JSON matching the schema and keep keys stable.\n"
            f"Schema hint: {json.dumps(schema_hint, ensure_ascii=True)}\n\n"
            "Document text:\n"
            f"{document_text[:20000]}\n\n"
            "Regulation context:\n"
            f"{context_text[:10000]}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )

        content = response.choices[0].message.content if response.choices else "{}"
        return _safe_json_loads(content)

    def legal_analysis(self, document_text: str, contexts: List[Dict]) -> Dict:
        schema_hint = {
            "score": 0,
            "summary": "",
            "red_flags": [""],
            "missing_fields": [""],
            "document_validity": "valid|uncertain|invalid",
            "recommendations": [""],
            "evidence": [""],
        }
        raw = self._call_json("legal", schema_hint, document_text, contexts)
        return validate_module_output("legal", raw)

    def risk_analysis(self, document_text: str, contexts: List[Dict]) -> Dict:
        schema_hint = {
            "score": 0,
            "summary": "",
            "risk_level": "low|medium|high",
            "construction_findings": [""],
            "material_concerns": [""],
            "structural_concerns": [""],
            "recommendations": [""],
            "evidence": [""],
        }
        raw = self._call_json("risk", schema_hint, document_text, contexts)
        return validate_module_output("risk", raw)

    def valuation_analysis(self, document_text: str, contexts: List[Dict]) -> Dict:
        schema_hint = {
            "score": 0,
            "summary": "",
            "price_fairness": "bargain|fair|inflated|insufficient_data",
            "estimated_value_range": {"min": 0, "max": 0, "currency": "TND"},
            "roi_estimate": {"annual_percent": 0, "confidence": "low|medium|high"},
            "recommendations": [""],
            "evidence": [""],
        }
        raw = self._call_json("valuation", schema_hint, document_text, contexts)
        return validate_module_output("valuation", raw)

    def final_due_diligence(
        self,
        document_text: str,
        contexts: List[Dict],
        legal_json: Dict,
        risk_json: Dict,
        valuation_json: Dict,
    ) -> Dict:
        self._ensure_client()
        schema_hint = {
            "overall_score": 0,
            "overall_risk": "low|medium|high",
            "go_no_go": "go|conditional_go|no_go",
            "top_issues": [""],
            "next_actions": [""],
            "confidence": "low|medium|high",
            "module_scores": {
                "legal": 0,
                "risk": 0,
                "valuation": 0,
            },
        }

        combined_payload = {
            "legal": legal_json,
            "risk": risk_json,
            "valuation": valuation_json,
        }

        context_text = self._contexts_to_text(contexts)
        user_prompt = (
            "Task: synthesize a complete final due diligence decision for this property.\n"
            "Return ONLY valid JSON matching the schema and keep keys stable.\n"
            f"Schema hint: {json.dumps(schema_hint, ensure_ascii=True)}\n\n"
            f"Module outputs: {json.dumps(combined_payload, ensure_ascii=True)}\n\n"
            "Document text excerpt:\n"
            f"{document_text[:10000]}\n\n"
            "Regulation context excerpt:\n"
            f"{context_text[:5000]}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )

        content = response.choices[0].message.content if response.choices else "{}"
        raw = _safe_json_loads(content)
        return validate_module_output("final", raw)


analysis_intelligence_service = AnalysisIntelligenceService()
