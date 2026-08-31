from fastapi import APIRouter, Depends, Body
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.schema.prev_employment import PrevEmployment
from api.handlers.prev_employment_handler import PrevEmploymentHandler
from api.pydantic_models.prev_employment import ReadPrevEmploymentCreate
from api.security import get_current_student

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

@router.get("/prev_employments", response_model=list[ReadPrevEmploymentCreate])
def get_prev_employments(
        session: Session = Depends(get_db),
        user=Depends(get_current_student)
):
    return PrevEmploymentHandler(session).get_user_prev_employments(user["sub"])