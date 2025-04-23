from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlmodel import Session

from app.handlers.employee_handler import EmployeeHandler
from app.pydantic_models.employee import EmployeeUpdate, EmployeeRead
from app.db.dependencies import get_db
from app.security import get_current_student,get_current_supervisor  # Import the dependency for student authentication

router = APIRouter()


def get_employee_handler(db: Session = Depends(get_db)) -> EmployeeHandler:
    return EmployeeHandler(db)


@router.patch("/employees/", response_model=EmployeeRead)
def update_employee_by_user(
    employee_data: EmployeeUpdate,
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Update an employee record by the user ID (user_account).
    """
    # Use the handler to get the employee by user_account
    employee = handler.get_employee_by_user_account(user.get("sub"))
    updated_employee = handler.update_employee(employee.id, employee_data.dict(exclude_unset=True))
    return updated_employee


@router.get("/employees/", response_model=EmployeeRead)
def get_employee_by_user(
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_supervisor),  # Secure the endpoint
):
    """
    Retrieve an employee record by the user ID (user_account).
    """
    employee = handler.get_employee_by_user_account(user.get("sub"))
    return employee


@router.delete("/employees/")
def delete_employee_by_user(
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_supervisor),  # Secure the endpoint
):
    """
    Delete an employee by the user ID (user_account).
    """
    result = handler.delete_employee_by_user_account(user.get("sub"))
    return result