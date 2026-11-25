import uuid
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile
from starlette.responses import FileResponse

from api.db.managers.dependencies import (
    get_specified_petition,
    get_specified_prev_employment,
)
from api.db.schema import Petition
from api.db.schema.prev_employment import PrevEmployment
from api.handlers import EmployeeHandler
from api.handlers.dependencies import get_employee_handler, get_prev_employment_handler
from api.handlers.prev_employment_handler import PrevEmploymentHandler
from api.pydantic_models.prev_employment import (
    PrevEmploymentRead,
    PrevEmploymentUpdate,
)
from api.security import get_current_clerk, get_current_student
from api.utils import PREV_EMPLOYMENTS_DIR, file_response

# from api.pydantic_models.prev_employment import PrevEmploymentCreate

router = APIRouter()


@router.post("/prev_employments", response_model=PrevEmployment)
def create_new_employment(
    body: dict = Body(...),
    user=Depends(get_current_student),
    prev_employment_handler: PrevEmploymentHandler = Depends(
        get_prev_employment_handler
    ),
):
    return prev_employment_handler.create_prev_employment(body, user["sub"])


@router.get("/prev_employments", response_model=list[PrevEmploymentRead])
def get_prev_employments(
    user=Depends(get_current_student),
    prev_employment_handler: PrevEmploymentHandler = Depends(
        get_prev_employment_handler
    ),
):
    return prev_employment_handler.get_user_prev_employments(user["sub"])


@router.patch(
    "/prev_employments/{prev_employment_id}/proof", response_model=PrevEmployment
)
def upload_proof(
    prev_employment_id: uuid.UUID,
    proof: UploadFile,
    user=Depends(get_current_student),
    prev_employment_handler: PrevEmploymentHandler = Depends(
        get_prev_employment_handler
    ),
):
    return prev_employment_handler.upload_file(proof)


@router.delete("/prev_employments/{prev_employment_id}", status_code=204)
def delete_prev_employment(
    prev_employment_id: uuid.UUID,
    user=Depends(get_current_student),
    prev_employment_handler: PrevEmploymentHandler = Depends(
        get_prev_employment_handler
    ),
):
    prev_employment_handler.delete_prev_employment()


@router.patch("/prev_employments/{prev_employment_id}", response_model=PrevEmployment)
def update_prev_employment(
    prev_employment_id: uuid.UUID,
    body: PrevEmploymentUpdate,
    user=Depends(get_current_student),
    prev_employment_handler: PrevEmploymentHandler = Depends(
        get_prev_employment_handler
    ),
):
    return prev_employment_handler.update_prev_employment(body)


# TODO: Refactor when we refactor how users ar distinguished in hr-login-backend
@router.get(
    "/clerk/prev_employments/petition/{petition_id}",
    response_model=list[PrevEmploymentRead],
)
def get_petitions_employees_employments(
    petition_id: uuid.UUID,
    user=Depends(get_current_clerk),
    petition: Petition = Depends(get_specified_petition),
    employee_handler: EmployeeHandler = Depends(get_employee_handler),
    prev_employment_handler: PrevEmploymentHandler = Depends(
        get_prev_employment_handler
    ),
):
    employee = employee_handler.get_employee_by_username(petition.student_username)
    return prev_employment_handler.get_user_prev_employments(employee.user_account)


@router.get(
    "/clerk/prev_employments/{prev_employment_id}/download", response_class=FileResponse
)
def download_prev_employment_proof(
    prev_employment_id: uuid.UUID,
    user=Depends(get_current_clerk),
    prev_employmeent: PrevEmployment = Depends(get_specified_prev_employment),
):
    if not prev_employmeent.proof:
        raise HTTPException(
            status_code=404,
            detail=f"Not file found for this entry.",
        )
    return file_response(
        PREV_EMPLOYMENTS_DIR,
        prev_employmeent.proof,
        f"proof{Path(prev_employmeent.proof).suffix}",
    )
