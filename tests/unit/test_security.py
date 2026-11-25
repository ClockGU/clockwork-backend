import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import api.security as security
from api.db.dependencies import get_db
from api.security import (
    UserRole,
    get_current_clerk,
    get_current_student,
    get_current_supervisor,
)

ROLE_DEPENDENCIES = {
    UserRole.STUDENT: get_current_student,
    UserRole.SUPERVISOR: get_current_supervisor,
    UserRole.CLERK: get_current_clerk,
}


class _ExistingEmployeeHandler:
    """Stands in for EmployeeHandler so get_current_student needs no database."""

    def __init__(self, db):
        pass

    def employee_exists_by_user_account(self, user_account):
        return True


@pytest.fixture(scope="module")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def client(private_key, monkeypatch):
    public_pem = (
        private_key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    monkeypatch.setattr(security, "PUBLIC_KEY", public_pem)
    monkeypatch.setattr(
        security, "EmployeeHandler", _ExistingEmployeeHandler, raising=False
    )

    app = FastAPI()
    for role, dependency in ROLE_DEPENDENCIES.items():

        def endpoint(user: dict = Depends(dependency)):
            return user

        app.add_api_route(f"/{role.name.lower()}", endpoint)
    app.dependency_overrides[get_db] = lambda: None
    return TestClient(app)


def make_token(private_key, role: UserRole, expires_in: int = 60) -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "username": "testuser",
        "user_role": role.value,
        "exp": int(time.time()) + expires_in,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("role", list(UserRole))
def test_matching_role_returns_payload(client, private_key, role):
    response = client.get(
        f"/{role.name.lower()}", headers=bearer(make_token(private_key, role))
    )
    assert response.status_code == 200
    assert response.json()["user_role"] == role.value


@pytest.mark.parametrize("role", list(UserRole))
def test_other_role_is_forbidden(client, private_key, role):
    other_role = next(r for r in UserRole if r != role)
    response = client.get(
        f"/{role.name.lower()}", headers=bearer(make_token(private_key, other_role))
    )
    assert response.status_code == 403


@pytest.mark.parametrize("role", list(UserRole))
def test_missing_header_is_unauthorized(client, role):
    response = client.get(f"/{role.name.lower()}")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "header", ["Bearer", "Bearer a b"], ids=["no_token", "extra_part"]
)
@pytest.mark.parametrize("role", list(UserRole))
def test_malformed_header_is_bad_request(client, role, header):
    response = client.get(f"/{role.name.lower()}", headers={"Authorization": header})
    assert response.status_code == 400


@pytest.mark.parametrize("role", list(UserRole))
def test_invalid_token_is_unauthorized(client, role):
    response = client.get(f"/{role.name.lower()}", headers=bearer("not-a-jwt"))
    assert response.status_code == 401


@pytest.mark.parametrize("role", list(UserRole))
def test_expired_token_is_unauthorized(client, private_key, role):
    token = make_token(private_key, role, expires_in=-60)
    response = client.get(f"/{role.name.lower()}", headers=bearer(token))
    assert response.status_code == 401
