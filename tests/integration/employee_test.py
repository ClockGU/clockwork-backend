import uuid

from sqlmodel import select

from api.db.schema.employee import Employee


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
