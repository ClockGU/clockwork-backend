import uuid
from datetime import date

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.db.dependencies import get_db
from api.db.managers.dependencies import (
    get_specified_employee,
    get_specified_petition,
    get_specified_prev_employment,
    get_specified_student_document,
)
from api.db.schema.prev_employment import PrevEmployment
from api.security import UserRole, decode_user_jwt

# Minimal app: one route per loader, so only the loader decides 200 vs 404.
loader_app = FastAPI()


@loader_app.get("/petition/{petition_id}")
def _petition(obj=Depends(get_specified_petition)):
    return {"id": str(obj.id)}


@loader_app.get("/employee/{employee_id}")
def _employee(obj=Depends(get_specified_employee)):
    return {"id": str(obj.id)}


@loader_app.get("/prev_employment/{prev_employment_id}")
def _prev_employment(obj=Depends(get_specified_prev_employment)):
    return {"id": str(obj.id)}


@loader_app.get("/document/{document_id}")
def _document(obj=Depends(get_specified_student_document)):
    return {"id": str(obj.id)}


@pytest.fixture
def prev_employment(db_session, student_employee):
    prev = PrevEmployment(
        user_account=student_employee.user_account,
        start=date(2024, 1, 1),
        end=date(2024, 6, 30),
        employer_name="Old Employer",
    )
    db_session.add(prev)
    db_session.flush()
    return prev


@pytest.fixture
def urls(petition_student_action, student_employee, student_documents, prev_employment):
    return {
        "petition": f"/petition/{petition_student_action.id}",
        "employee": f"/employee/{student_employee.id}",
        "prev_employment": f"/prev_employment/{prev_employment.id}",
        "document": f"/document/{student_documents.id}",
    }


@pytest.fixture
def users(petition_student_action, student_employee):
    def payload(sub, username, role):
        return {"sub": str(sub), "username": username, "user_role": role.value}

    return {
        "owning_student": payload(
            student_employee.user_account, student_employee.username, UserRole.STUDENT
        ),
        "other_student": payload(uuid.uuid4(), "otherstudent", UserRole.STUDENT),
        "owning_supervisor": payload(
            petition_student_action.user_account, "supervisor", UserRole.SUPERVISOR
        ),
        "other_supervisor": payload(
            uuid.uuid4(), "othersupervisor", UserRole.SUPERVISOR
        ),
        "clerk": payload(uuid.uuid4(), "clerk", UserRole.CLERK),
    }


@pytest.fixture
def as_user(db_session):
    """Return a TestClient for the loader app, authenticated with the given JWT payload."""

    def _as(payload: dict) -> TestClient:
        loader_app.dependency_overrides[get_db] = lambda: db_session
        loader_app.dependency_overrides[decode_user_jwt] = lambda: payload
        return TestClient(loader_app)

    yield _as
    loader_app.dependency_overrides.clear()


CASES = [
    # Petition: supervisor owns via user_account, student via student_username.
    ("petition", "owning_supervisor", 200),
    ("petition", "other_supervisor", 404),
    ("petition", "owning_student", 200),
    ("petition", "other_student", 404),
    ("petition", "clerk", 200),
    # Student-owned schemas: owner via user_account.
    ("employee", "owning_student", 200),
    ("employee", "other_student", 404),
    ("employee", "clerk", 200),
    ("prev_employment", "owning_student", 200),
    ("prev_employment", "other_student", 404),
    ("prev_employment", "clerk", 200),
    ("document", "owning_student", 200),
    ("document", "other_student", 404),
    ("document", "clerk", 200),
]


@pytest.mark.parametrize(
    "resource, user, expected_status",
    CASES,
    ids=[f"{resource}-{user}-{status}" for resource, user, status in CASES],
)
def test_loader_checks_ownership(as_user, urls, users, resource, user, expected_status):
    response = as_user(users[user]).get(urls[resource])

    assert response.status_code == expected_status
