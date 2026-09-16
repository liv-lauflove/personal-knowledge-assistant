from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth import get_current_user_id
from app.database import get_db
from app.documents.services import MAX_FILE_SIZE, validate_file_content
from app.main import app
from app.models import DocumentStatus, User, Workspace

# --- Unit Tests: validate_file_content ---


def test_validate_pdf_success():
    valid_pdf = b"%PDF-1.5 \n%trailer\n%%EOF"
    mime = validate_file_content(valid_pdf, "sample.pdf")
    assert mime == "application/pdf"


def test_validate_txt_success():
    valid_txt = "Hello world! This is a test document.".encode("utf-8")
    mime = validate_file_content(valid_txt, "notes.txt")
    assert mime == "text/plain"


def test_validate_empty_file_fails():
    with pytest.raises(HTTPException) as exc_info:
        validate_file_content(b"", "empty.txt")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "EMPTY_FILE"


def test_validate_file_too_large_fails():
    large_content = b"a" * (MAX_FILE_SIZE + 1)
    with pytest.raises(HTTPException) as exc_info:
        validate_file_content(large_content, "huge.txt")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "FILE_TOO_LARGE"


def test_validate_binary_png_disguised_as_txt_fails():
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    with pytest.raises(HTTPException) as exc_info:
        validate_file_content(fake_png, "fake.txt")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "INVALID_FILE_TYPE"


def test_validate_txt_with_null_bytes_fails():
    corrupted_txt = b"Hello\x00World"
    with pytest.raises(HTTPException) as exc_info:
        validate_file_content(corrupted_txt, "corrupt.txt")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "INVALID_FILE_TYPE"


def test_validate_invalid_utf8_fails():
    invalid_utf8 = b"\x80\x81\x82\x83\x84"
    with pytest.raises(HTTPException) as exc_info:
        validate_file_content(invalid_utf8, "bad_encoding.txt")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "UNSUPPORTED_ENCODING"


# --- Integration Tests: POST /api/v1/documents/upload ---


@pytest.fixture
def mock_db_session():
    db = MagicMock()
    # Mock User query
    user = User(id="user_123", name="Test User", email="test@example.com")
    workspace = Workspace(id="ws_123", user_id="user_123", name="Default Workspace")

    def query_side_effect(model):
        query_mock = MagicMock()
        if model == User:
            query_mock.filter.return_value.first.return_value = user
        elif model == Workspace:
            query_mock.filter.return_value.first.return_value = workspace
            query_mock.filter.return_value.order_by.return_value.first.return_value = (
                workspace
            )
        return query_mock

    db.query.side_effect = query_side_effect
    return db


@pytest.fixture
def client(mock_db_session):
    app.dependency_overrides[get_current_user_id] = lambda: "user_123"
    app.dependency_overrides[get_db] = lambda: mock_db_session

    yield TestClient(app)

    app.dependency_overrides.clear()


@patch("app.documents.services.upload_file")
def test_upload_pdf_endpoint_success(mock_upload, client, mock_db_session):
    mock_upload.return_value = "ws_123/doc_id_test.pdf"

    pdf_content = b"%PDF-1.4 Minimal PDF header content"
    files = {"file": ("document.pdf", pdf_content, "application/pdf")}

    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "document.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["status"] == DocumentStatus.PENDING.value
    assert data["workspace_id"] == "ws_123"
    assert mock_upload.called


@patch("app.documents.services.upload_file")
def test_upload_txt_endpoint_success(mock_upload, client, mock_db_session):
    mock_upload.return_value = "ws_123/doc_id_notes.txt"

    txt_content = b"This is a valid plain text note."
    files = {"file": ("notes.txt", txt_content, "text/plain")}

    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "notes.txt"
    assert data["mime_type"] == "text/plain"
    assert data["status"] == DocumentStatus.PENDING.value
    assert mock_upload.called


def test_upload_invalid_file_type_fails(client):
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    files = {"file": ("malicious.txt", fake_png, "text/plain")}

    response = client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"]["code"] == "INVALID_FILE_TYPE"
