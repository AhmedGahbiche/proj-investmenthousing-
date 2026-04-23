"""Core API and upload service tests."""

import os

# Configure runtime before app modules import settings.
os.environ.setdefault("AUTH_REQUIRED", "False")
os.environ.setdefault("SKIP_DEPENDENCY_CHECK", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_document_management.db")
os.environ.setdefault("UPLOAD_DIR", "./test_uploads")

from fastapi.testclient import TestClient

from main import app
from services.upload_service import upload_service


client = TestClient(app)


def test_health_check() -> None:
	response = client.get("/health")
	assert response.status_code == 200
	payload = response.json()
	assert payload["status"] == "healthy"
	assert payload["service"]


def test_validate_file_success() -> None:
	is_valid, error = upload_service.validate_file("doc.txt", b"hello")
	assert is_valid is True
	assert error == ""


def test_validate_file_empty_content() -> None:
	is_valid, error = upload_service.validate_file("doc.txt", b"")
	assert is_valid is False
	assert "empty" in error.lower()


def test_upload_endpoint_returns_success_with_stubbed_service(monkeypatch) -> None:
	def fake_process_upload(**kwargs):
		return {
			"success": True,
			"message": "Document uploaded and processed successfully",
			"document_id": 123,
			"filename": kwargs["filename"],
			"error": None,
		}

	monkeypatch.setattr(upload_service, "process_upload", fake_process_upload)

	response = client.post(
		"/upload",
		files={"file": ("stub.txt", b"stub content", "text/plain")},
	)
	assert response.status_code == 200
	payload = response.json()
	assert payload["success"] is True
	assert payload["document_id"] == 123


def test_upload_endpoint_rejects_empty_file() -> None:
	response = client.post(
		"/upload",
		files={"file": ("empty.txt", b"", "text/plain")},
	)
	assert response.status_code == 400
	payload = response.json()
	assert payload.get("error")
