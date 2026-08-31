from fastapi import APIRouter, Depends, Body
from sqlmodel import Session

from api.db.dependencies import get_db
from api.handlers.prev_employment_handler import PrevEmploymentHandler
from api.security import get_current_student

# from api.pydantic_models.prev_employment import PrevEmploymentCreate

router = APIRouter()

@router.post("/prev_employments")
def create_new_employment(
    body: dict = Body(...),
    session: Session = Depends(get_db),
    user=Depends(get_current_student),
):
    response = PrevEmploymentHandler(session).create_prev_employment(body, user["sub"])
    return response