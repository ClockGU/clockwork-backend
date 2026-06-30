import uuid
from datetime import date
from typing import List, Optional

from sqlmodel import SQLModel

from api.consts import PetitionStatus
from api.pydantic_models.budget_position import BudgetPositionBase


class PetitionExceptionBase(SQLModel):
    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    time_exce_time: Optional[int] = None

    duration_exce_course: Optional[bool] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None


class PetitionBase(SQLModel, PetitionExceptionBase):
    """
    Base model for Petition with common fields used for validation.
    """

    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int
    ba_degree: bool

    student_username: str
    supervisor_mail: Optional[str] = None

    budget_positions: List[BudgetPositionBase]

    status: PetitionStatus = PetitionStatus.SUPERVISOR_ACTION
