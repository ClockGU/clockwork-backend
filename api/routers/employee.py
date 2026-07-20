from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from api.handlers.employee_handler import EmployeeHandler
from api.handlers.dependencies import get_employee_handler
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
    updated_employee = handler.update_employee(
        employee_data.dict(exclude_unset=True)
    )
    return updated_employee


@router.get("/employees", response_model=EmployeeRead)
def get_employee_by_user(
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_student),
):
    """
    Retrieve an employee record by the user ID (user_account).
    """
    employee = handler.get_employee_by_user_account(user.get("sub"))
    return employee


@router.get("/employees/student-data-pdf")
def get_student_data_pdf(
    petition_id: UUID = Query(..., description="Petition ID"),
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_clerk),
):
    """
    Get student data PDF for a given petition ID.
    Derived the student username from the petition.
    """
    # Generate PDF
    pdf_buffer = handler.get_student_data_pdf(petition_id)

    # Get employee for filename
    employee = handler.get_employee_by_petition(petition_id)
    filename = f"Student_Data_{employee.last_name}_{employee.first_name}_{date.today().strftime('%d-%m-%Y')}.pdf"

    # Return as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

# Todo: This endpoint and the related handler method revolves around a petition id rather than the actual employee entry
# Should be refactored to the /petitions endpoints
@router.get("/employees/petition/{petition_id}", response_model=EmployeeRead)
def get_employee_by_petition_id(
    petition_id: UUID,
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_clerk),
):
    """
    Retrieve an employee record by the petition ID.
    Only accessible by CLERK role.
    """
    employee = handler.get_employee_by_petition(petition_id)
    return employee
