from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from uuid import UUID
from sqlmodel import Session
from datetime import date

from api.handlers.employee_handler import EmployeeHandler
from api.pydantic_models.employee import EmployeeUpdate, EmployeeRead
from api.db.dependencies import get_db
from api.security import get_current_student,get_current_supervisor  # Import the dependency for student authentication

router = APIRouter()


def get_employee_handler(db: Session = Depends(get_db)) -> EmployeeHandler:
    return EmployeeHandler(db)


@router.patch("/employees/", response_model=EmployeeRead)
def update_employee_by_user(
    employee_data: EmployeeUpdate,
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_student),  
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
    user=Depends(get_current_student), 
):
    """
    Retrieve an employee record by the user ID (user_account).
    """
    employee = handler.get_employee_by_user_account(user.get("sub"))
    return employee


@router.delete("/employees/")
def delete_employee_by_user(
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Delete an employee by the user ID (user_account).
    """
    result = handler.delete_employee_by_user_account(user.get("sub"))
    return result


@router.get("/employees/student-data-pdf")
def get_student_data_pdf(
    petition_id: UUID = Query(..., description="Petition ID"),
    handler: EmployeeHandler = Depends(get_employee_handler),
    user=Depends(get_current_supervisor),
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
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )