"""
Pydantic validation schemas for OpenAI module outputs.

Each module schema mirrors the schema_hint passed to the model.
Validation is intentionally lenient (all fields Optional) so a partially
valid response still passes with warnings rather than raising hard errors.
The goal is detecting structurally wrong responses, not enforcing every field.
"""
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class LegalOutputSchema(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=100)
    summary: Optional[str] = None
    red_flags: Optional[List[str]] = None
    missing_fields: Optional[List[str]] = None
    document_validity: Optional[Literal["valid", "uncertain", "invalid"]] = None
    recommendations: Optional[List[str]] = None
    evidence: Optional[List[str]] = None

    @field_validator("score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class RiskOutputSchema(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=100)
    summary: Optional[str] = None
    risk_level: Optional[Literal["low", "medium", "high"]] = None
    construction_findings: Optional[List[str]] = None
    material_concerns: Optional[List[str]] = None
    structural_concerns: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    evidence: Optional[List[str]] = None

    @field_validator("score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class ValuationRangeSchema(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = None


class ROIEstimateSchema(BaseModel):
    annual_percent: Optional[float] = None
    confidence: Optional[Literal["low", "medium", "high"]] = None


class ValuationOutputSchema(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=100)
    summary: Optional[str] = None
    price_fairness: Optional[Literal["bargain", "fair", "inflated", "insufficient_data"]] = None
    estimated_value_range: Optional[ValuationRangeSchema] = None
    roi_estimate: Optional[ROIEstimateSchema] = None
    recommendations: Optional[List[str]] = None
    evidence: Optional[List[str]] = None

    @field_validator("score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class ModuleScoresSchema(BaseModel):
    legal: Optional[float] = None
    risk: Optional[float] = None
    valuation: Optional[float] = None


class FinalOutputSchema(BaseModel):
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    overall_risk: Optional[Literal["low", "medium", "high"]] = None
    go_no_go: Optional[Literal["go", "conditional_go", "no_go"]] = None
    top_issues: Optional[List[str]] = None
    next_actions: Optional[List[str]] = None
    confidence: Optional[Literal["low", "medium", "high"]] = None
    module_scores: Optional[ModuleScoresSchema] = None

    @field_validator("overall_score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


_MODULE_SCHEMAS = {
    "legal": LegalOutputSchema,
    "risk": RiskOutputSchema,
    "valuation": ValuationOutputSchema,
    "final": FinalOutputSchema,
}


def validate_module_output(module_name: str, raw: dict) -> dict:
    """
    Validate raw module output dict against its schema.

    On success: returns the validated dict (model.model_dump()).
    On failure: returns the original dict annotated with '_validation_errors'
    so operators can detect bad payloads without the pipeline crashing.

    Args:
        module_name: One of 'legal', 'risk', 'valuation', 'final'.
        raw: Parsed dict from the model response.

    Returns:
        Validated (or annotated) dict safe to persist.
    """
    import logging
    logger = logging.getLogger(__name__)

    schema_cls = _MODULE_SCHEMAS.get(module_name)
    if schema_cls is None:
        return raw

    # Short-circuit: if raw already has a 'status'='partial' error marker from
    # _resolve_module_result, skip schema validation — the module did not produce output.
    if raw.get("status") == "partial":
        return raw

    try:
        validated = schema_cls.model_validate(raw)
        return validated.model_dump(exclude_none=False)
    except Exception as exc:
        errors = str(exc)
        logger.warning(
            "Schema validation failed for module '%s': %s — storing raw output with error annotation",
            module_name, errors,
        )
        annotated = dict(raw)
        annotated["_validation_errors"] = errors
        return annotated
