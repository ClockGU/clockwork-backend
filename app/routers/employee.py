from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlmodel import Session

from app.handlers.employee_handler import EmployeeHandler
from app.pydantic_models.employee import EmployeeUpdate, EmployeeRead
from app.db.dependencies import get_db
from app.security import get_current_student  # Import the dependency for student authentication

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
    employee = handler.get_employee_by_user_account(user.get("id"))
    updated_employee = handler.update_employee(employee.id, employee_data.dict(exclude_unset=True))
    return updated_employee


@router.get("/employees/", response_model=EmployeeRead)
def get_employee_by_user(
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Retrieve an employee record by the user ID (user_account).
    """
    import remote_pdb; remote_pdb.set_trace("0.0.0.0", 4444)
    employee = handler.get_employee_by_user_account(user.get("id"))
    return employee