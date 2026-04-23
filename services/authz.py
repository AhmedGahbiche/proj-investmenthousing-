"""Authorization helpers for resource-level access control."""

from typing import Any

from fastapi import HTTPException, Request

from config import settings


def _normalize_csv_values(raw_value: Any) -> set[str]:
    if raw_value is None:
        return set()

    if isinstance(raw_value, str):
        values = raw_value.split(",")
    elif isinstance(raw_value, (list, tuple, set)):
        values = [str(value) for value in raw_value]
    else:
        values = [str(raw_value)]

    return {value.strip() for value in values if value and value.strip()}


def get_session_payload(request: Request) -> dict[str, Any]:
    session = getattr(request.state, "session", None)
    if isinstance(session, dict):
        return session
    return {}


def is_admin(session: dict[str, Any]) -> bool:
    return str(session.get("role", "")).lower() == "admin"


def get_allowed_property_ids(session: dict[str, Any]) -> set[str]:
    from_token = _normalize_csv_values(session.get("property_ids"))
    if from_token:
        return from_token

    return _normalize_csv_values(settings.CLIENT_ALLOWED_PROPERTY_IDS)


def ensure_document_access(request: Request, document: Any) -> None:
    """Enforce that non-admin users can only access configured property scopes."""
    session = get_session_payload(request)
    if is_admin(session):
        return

    if str(session.get("role", "")).lower() != "client":
        raise HTTPException(status_code=403, detail="Forbidden")

    document_property_id = str(getattr(document, "property_id", "") or "").strip()
    if not document_property_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    allowed_property_ids = get_allowed_property_ids(session)
    if not allowed_property_ids or document_property_id not in allowed_property_ids:
        raise HTTPException(status_code=403, detail="Forbidden")
