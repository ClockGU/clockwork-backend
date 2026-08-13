from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from api.handlers.dependencies import get_employee_handler
from api.handlers.employee_handler import EmployeeHandler
from api.pydantic_models.employee import EmployeeRead, EmployeeUpdate
from api.security import (  # Import the dependency for student authentication
    get_current_clerk,
    get_current_student,
)

router = APIRouter()


@router.patch("/employees", response_model=EmployeeRead)
def update_employee_by_user(
    employee_data: EmployeeUpdate,
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_student),
):
    """
    Update an employee record by the user ID (user_account).
    """
    updated_employee = handler.update_employee(employee_data.dict(exclude_unset=True))
    return updated_employee


@router.get("/employees/me", response_model=EmployeeRead)
def get_employee_by_user(
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_student),
):
    """
    Retrieve an employee record by the user ID (user_account).
    """
    employee = handler.get_employee_by_user_account(user.get("sub"))
    return employee


# Todo: This endpoint and the related handler method revolves around a petition id rather than the actual employee entry
# Should be refactored to the /petitions endpoints
@router.get("/employees/{username}", response_model=EmployeeRead)
def get_employee_by_petition_id(
    username: str,
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_clerk),
):
    """
    Retrieve an employee record by the petition ID.
    Only accessible by CLERK role.
    """
    employee = handler.get_employee_by_username(username)
    return employee
