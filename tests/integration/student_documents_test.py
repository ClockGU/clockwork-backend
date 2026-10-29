import uuid

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

import api.security
from api.db.schema.employee import Employee
from api.db.schema.student_documents import StudentDocuments
from api.main import app
from api.security import UserRole, decode_user_jwt, get_current_clerk, get_current_student


@pytest.fixture
def as_student(student_employee):
    app.dependency_overrides[get_current_student] = lambda: {
        "sub": str(student_employee.user_account)
    }
    yield
    app.dependency_overrides.pop(get_current_student, None)


@pytest.fixture
def as_clerk():
    app.dependency_overrides[get_current_clerk] = lambda: {"sub": str(uuid.uuid4())}
    yield
    app.dependency_overrides.pop(get_current_clerk, None)


def test_clerk_gets_documents_for_petition(
    client, student_documents, petition_student_action, as_clerk
):
    response = client.get(f"/clerk/petitions/{petition_student_action.id}/documents")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(student_documents.id)
    assert data["user_account"] == str(student_documents.user_account)


def test_non_clerk_cannot_get_documents_for_petition(
    client, student_documents, petition_student_action
):
    app.dependency_overrides[decode_user_jwt] = lambda: {
        "sub": str(uuid.uuid4()),
        "user_role": UserRole.STUDENT.value,
    }
    try:
        response = client.get(
            f"/clerk/petitions/{petition_student_action.id}/documents"
        )
    finally:
        app.dependency_overrides.pop(decode_user_jwt, None)

    assert response.status_code == 403


def test_documents_for_unknown_petition_returns_404(client, as_clerk):
    response = client.get(f"/clerk/petitions/{uuid.uuid4()}/documents")

    assert response.status_code == 404


def test_documents_for_petition_without_documents_returns_404(
    client, student_employee, petition_student_action, as_clerk
):
    response = client.get(f"/clerk/petitions/{petition_student_action.id}/documents")

    assert response.status_code == 404


def test_documents_by_username_endpoint_is_gone(client, student_documents, as_clerk):
    response = client.get(
        "/clerk/documents-by-username", params={"student_username": "teststudent"}
    )

    assert response.status_code == 404


def test_get_documents_returns_callers_document_without_employee_query(
    client, db_session, student_documents, as_student
):
    statements = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    connection = db_session.connection()
    event.listen(connection, "before_cursor_execute", record)
    try:
        response = client.get("/documents")
    finally:
        event.remove(connection, "before_cursor_execute", record)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(student_documents.id)
    assert data["user_account"] == str(student_documents.user_account)
    assert not [s for s in statements if "FROM employee" in s]


def test_employee_user_account_update_cascades_to_documents(
    db_session, student_documents, student_employee
):
    new_user_account = uuid.uuid4()
    db_session.execute(
        text("UPDATE employee SET user_account = :new WHERE id = :id"),
        {"new": new_user_account, "id": student_employee.id},
    )

    document_user_account = db_session.execute(
        text("SELECT user_account FROM studentdocuments WHERE id = :id"),
        {"id": student_documents.id},
    ).scalar_one()
    assert document_user_account == new_user_account


def test_document_with_unknown_user_account_fails(db_session):
    db_session.add(StudentDocuments(user_account=uuid.uuid4()))
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_first_login_creates_employee_and_documents(client, db_session, monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    monkeypatch.setattr(api.security, "public_key", public_pem)
    monkeypatch.setattr(api.security, "JWT_ALGORITHM", "RS256")

    user_account = uuid.uuid4()
    token = jwt.encode(
        {
            "sub": str(user_account),
            "username": "firstlogin",
            "user_role": UserRole.STUDENT.value,
        },
        private_key,
        algorithm="RS256",
    )

    response = client.get("/documents", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["user_account"] == str(user_account)
    employee = db_session.execute(
        select(Employee).where(Employee.user_account == user_account)
    ).scalar_one()
    assert employee.username == "firstlogin"
    document = db_session.execute(
        select(StudentDocuments).where(StudentDocuments.user_account == user_account)
    ).scalar_one()
    assert document.employee.id == employee.id


def test_get_documents_returns_file_keys(client, student_documents, as_student):
    response = client.get("/documents")

    assert response.status_code == 200
    data = response.json()
    assert data["elstam_file"] == "elstam.pdf"
    assert data["studienbescheinigung_file"] == "studien.pdf"
    assert data["versicherungsbescheinigung_file"] == "versicherung.pdf"
    assert data["sozialversicherungsbogen_file"] == "sozialversicherung.pdf"
    assert data["ba_degree_file"] is None
    assert data["residence_permit_file"] is None
    assert data["id_photo_file"] == "id_photo.jpg"
    assert not [key for key in data if key.endswith("_url")]
