from sqlmodel import SQLModel
from typing import Optional
from datetime import date
import uuid


from api.consts import PetitionStatus

## these pydantic models are for the manager of the petition
class PetitionBase(SQLModel):
    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int
    ba_degree: bool
    budget_position: str
    budget_approver: str
    student_username: str

    status: PetitionStatus = PetitionStatus.SUPERVISOR_ACTION

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

