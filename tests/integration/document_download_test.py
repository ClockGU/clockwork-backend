import uuid

import pytest

from api.env import settings
from api.main import app
from api.security import UserRole, decode_user_jwt
from api.utils import STUDENT_DOCUMENTS_DIR, create_upload_dirs

ELSTAM_CONTENT = b"%PDF-1.4 elstam content"


@pytest.fixture
def stored_elstam(tmp_path, monkeypatch, student_documents):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    create_upload_dirs()
    (tmp_path / STUDENT_DOCUMENTS_DIR / student_documents.elstam_file).write_bytes(
        ELSTAM_CONTENT
    )
    return student_documents


@pytest.fixture
def serve_via_nginx(monkeypatch):
    monkeypatch.setattr(settings, "SERVE_FILES_VIA_NGINX", True)


@pytest.fixture
def serve_via_fastapi(monkeypatch):
    monkeypatch.setattr(settings, "SERVE_FILES_VIA_NGINX", False)


def _login(sub, role):
    app.dependency_overrides[decode_user_jwt] = lambda: {
        "sub": str(sub),
        "user_role": role.value,
    }


@pytest.fixture
def as_owner(student_employee):
    _login(student_employee.user_account, UserRole.STUDENT)
    yield
    app.dependency_overrides.pop(decode_user_jwt, None)


@pytest.fixture
def as_other_student():
    _login(uuid.uuid4(), UserRole.STUDENT)
    yield
    app.dependency_overrides.pop(decode_user_jwt, None)


@pytest.fixture
def as_clerk():
    _login(uuid.uuid4(), UserRole.CLERK)
    yield
    app.dependency_overrides.pop(decode_user_jwt, None)


def test_owner_downloads_file(client, stored_elstam, serve_via_fastapi, as_owner):
    response = client.get(f"/documents/{stored_elstam.id}/elstam")

    assert response.status_code == 200
    assert response.content == ELSTAM_CONTENT


def test_clerk_downloads_file(client, stored_elstam, serve_via_fastapi, as_clerk):
    response = client.get(f"/documents/{stored_elstam.id}/elstam")

    assert response.status_code == 200
    assert response.content == ELSTAM_CONTENT


def test_other_student_gets_404(client, stored_elstam, as_other_student):
    response = client.get(f"/documents/{stored_elstam.id}/elstam")

    assert response.status_code == 404


def test_unknown_document_gets_404(client, as_clerk):
    response = client.get(f"/documents/{uuid.uuid4()}/elstam")

    assert response.status_code == 404


def test_empty_field_gets_404(client, stored_elstam, as_owner):
    response = client.get(f"/documents/{stored_elstam.id}/ba_degree")

    assert response.status_code == 404


def test_invalid_type_gets_422(client, stored_elstam, as_owner):
    response = client.get(f"/documents/{stored_elstam.id}/not_a_type")

    assert response.status_code == 422


@pytest.mark.parametrize("flag", [True, False])
def test_download_headers(client, stored_elstam, monkeypatch, as_owner, flag):
    monkeypatch.setattr(settings, "SERVE_FILES_VIA_NGINX", flag)

    response = client.get(f"/documents/{stored_elstam.id}/elstam")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == "attachment; filename*=UTF-8''elstam.pdf"
    )
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_nginx_flag_returns_accel_redirect_with_empty_body(
    client, stored_elstam, serve_via_nginx, as_owner
):
    response = client.get(f"/documents/{stored_elstam.id}/elstam")

    assert response.status_code == 200
    assert (
        response.headers["x-accel-redirect"]
        == f"/protected/{STUDENT_DOCUMENTS_DIR}/{stored_elstam.elstam_file}"
    )
    assert response.content == b""


def test_fastapi_serving_has_no_accel_redirect(
    client, stored_elstam, serve_via_fastapi, as_owner
):
    response = client.get(f"/documents/{stored_elstam.id}/elstam")

    assert "x-accel-redirect" not in response.headers


def test_download_file_endpoint_is_gone(client, stored_elstam):
    response = client.get(
        "/download-file", params={"file_url": stored_elstam.elstam_file}
    )

    assert response.status_code == 404
