import uuid
from datetime import date

import pytest

from api.db.schema.prev_employment import PrevEmployment
from api.env import settings
from api.main import app
from api.security import UserRole, decode_user_jwt
from api.utils import PREV_EMPLOYMENTS_DIR, create_upload_dirs

PROOF_CONTENT = b"%PDF-1.4 proof content"


def _prev_employment(db_session, proof):
    prev_employment = PrevEmployment(
        user_account=uuid.uuid4(),
        start=date(2024, 1, 1),
        end=date(2024, 6, 30),
        employer_name="Employer",
        proof=proof,
    )
    db_session.add(prev_employment)
    db_session.flush()
    return prev_employment


@pytest.fixture
def stored_proof(tmp_path, monkeypatch, db_session):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    create_upload_dirs()
    prev_employment = _prev_employment(db_session, f"{uuid.uuid4()}_proof.pdf")
    (tmp_path / PREV_EMPLOYMENTS_DIR / prev_employment.proof).write_bytes(
        PROOF_CONTENT
    )
    return prev_employment


@pytest.fixture
def without_proof(db_session):
    return _prev_employment(db_session, None)


def _login(role):
    app.dependency_overrides[decode_user_jwt] = lambda: {
        "sub": str(uuid.uuid4()),
        "user_role": role.value,
    }


@pytest.fixture
def as_clerk():
    _login(UserRole.CLERK)
    yield
    app.dependency_overrides.pop(decode_user_jwt, None)


@pytest.fixture
def as_student():
    _login(UserRole.STUDENT)
    yield
    app.dependency_overrides.pop(decode_user_jwt, None)


def _url(prev_employment):
    return f"/clerk/prev_employments/{prev_employment.id}/download"


def test_nginx_flag_returns_accel_redirect_with_empty_body(
    client, stored_proof, monkeypatch, as_clerk
):
    monkeypatch.setattr(settings, "SERVE_FILES_VIA_NGINX", True)

    response = client.get(_url(stored_proof))

    assert response.status_code == 200
    assert (
        response.headers["x-accel-redirect"]
        == f"/protected/{PREV_EMPLOYMENTS_DIR}/{stored_proof.proof}"
    )
    assert response.content == b""


def test_fastapi_serving_returns_file(client, stored_proof, monkeypatch, as_clerk):
    monkeypatch.setattr(settings, "SERVE_FILES_VIA_NGINX", False)

    response = client.get(_url(stored_proof))

    assert response.status_code == 200
    assert response.content == PROOF_CONTENT
    assert "x-accel-redirect" not in response.headers


@pytest.mark.parametrize("flag", [True, False])
def test_download_headers(client, stored_proof, monkeypatch, as_clerk, flag):
    monkeypatch.setattr(settings, "SERVE_FILES_VIA_NGINX", flag)

    response = client.get(_url(stored_proof))

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == "attachment; filename*=UTF-8''proof.pdf"
    )
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_no_proof_gets_404(client, without_proof, as_clerk):
    response = client.get(_url(without_proof))

    assert response.status_code == 404


def test_student_gets_403(client, stored_proof, as_student):
    response = client.get(_url(stored_proof))

    assert response.status_code == 403
