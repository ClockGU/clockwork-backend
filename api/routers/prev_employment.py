import uuid

from fastapi import APIRouter, Depends, Body, UploadFile, HTTPException
from sqlmodel import Session
from starlette.responses import FileResponse

from api.db.dependencies import get_db
from api.db.managers.dependencies import (
    get_specified_petition,
    get_specified_prev_employment,
)
from api.db.schema import Petition
from api.db.schema.prev_employment import PrevEmployment
from api.handlers import EmployeeHandler
from api.handlers.dependencies import get_employee_handler
from api.handlers.prev_employment_handler import PrevEmploymentHandler
from api.pydantic_models.prev_employment import (
    PrevEmploymentRead,
    PrevEmploymentUpdate,
)
from api.security import get_current_student, get_current_clerk
from api.utils import upload_file_path

# from api.pydantic_models.prev_employment import PrevEmploymentCreate

router = APIRouter()

@router.post("/prev_employments",response_model=PrevEmployment)
def create_new_employment(
    body: dict = Body(...),
    session: Session = Depends(get_db),
    user=Depends(get_current_student),
):
    response = PrevEmploymentHandler(session).create_prev_employment(body, user["sub"])
    return response

@router.get("/prev_employments", response_model=list[PrevEmploymentRead])
def get_prev_employments(
        session: Session = Depends(get_db),
        user=Depends(get_current_student)
):
    return PrevEmploymentHandler(session).get_user_prev_employments(user["sub"])

@router.patch("/prev_employments/{prev_employment_id}/proof", response_model=PrevEmployment)
def upload_proof(prev_employment_id: uuid.UUID, proof: UploadFile, session: Session = Depends(get_db)):
    return PrevEmploymentHandler(session).upload_file(prev_employment_id, proof)

@router.delete("/prev_employments/{prev_employment_id}", status_code=204)
def delete_prev_employment(prev_employment_id: uuid.UUID, session: Session = Depends(get_db)):
    PrevEmploymentHandler(session).delete_prev_employment(prev_employment_id)

@router.patch("/prev_employments/{prev_employment_id}", response_model=PrevEmployment)
def update_prev_employment(prev_employment_id: uuid.UUID, body: PrevEmploymentUpdate, session: Session = Depends(get_db)):
    return PrevEmploymentHandler(session).update_prev_employment(prev_employment_id, body)

# TODO: Refactor when we refactor how users ar distinguished in hr-login-backend
@router.get("/clerk/prev_employments/petition/{petition_id}", response_model=list[PrevEmploymentRead])
def get_petitions_employees_employments(
        petition_id: uuid.UUID,
        petition: Petition = Depends(get_specified_petition),
        employee_handler: EmployeeHandler = Depends(get_employee_handler),
        session: Session = Depends(get_db),
        user = Depends(get_current_clerk)
):
    employee = employee_handler.get_employee_by_username(petition.student_username)
    return PrevEmploymentHandler(session).get_user_prev_employments(employee.user_account)


@router.get("/clerk/prev_employments/{prev_employment_id}/download", response_class=FileResponse)
def download_prev_employment_proof(
        prev_employment_id: uuid.UUID,
        prev_employmeent: PrevEmployment = Depends(get_specified_prev_employment),
        user = Depends(get_current_clerk)
):
    if not prev_employmeent.proof:
        raise HTTPException(
            status_code=404,
            detail=f"Not file found for this entry.",
        )
    return upload_file_path(prev_employmeent.proof)