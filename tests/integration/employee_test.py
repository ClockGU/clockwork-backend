import uuid

import pytest
from sqlmodel import select

from api.db.schema.employee import Employee
from api.main import app
from api.security import get_current_student, decode_user_jwt

@pytest.fixture
def as_student_payload():
    """Authenticate as a student with the given JWT payload, bypassing token checks."""

    def _as(payload: dict):
        app.dependency_overrides[decode_user_jwt]= lambda: payload


    yield _as
    app.dependency_overrides.pop(get_current_student, None)


def test_employees_me_creates_employeeon_first_call(
    client, db_session, as_student_payload
):
    user_account = uuid.uuid4()
    as_student_payload({"sub": str(user_account), "username": "firstlogin", "user_role":0})

    response = client.get("/employees/me")

    assert response.status_code == 200
    assert response.json()["username"] == "firstlogin"
    employee = db_session.execute(
        select(Employee).where(Employee.user_account == user_account)
    ).scalar_one()
    assert str(employee.id) == response.json()["id"]


def test_employees_me_returns_existing_employee_without_duplicates(
    client, db_session, student_employee, student_documents, as_student_payload
):
    as_student_payload(
        {"sub": str(student_employee.user_account), "username": "teststudent", "user_role":0}
    )

    response = client.get("/employees/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(student_employee.id)
    employees = db_session.execute(
        select(Employee).where(Employee.user_account == student_employee.user_account)
    ).all()
    assert len(employees) == 1
