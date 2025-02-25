
from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import date


class PetitionBase(SQLModel):
    user_account: str
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int
    ba_degree: str
    budget_position: str
    budget_approver: str
    student_mail: str
    time_exce_student: Optional[str] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    duration_exce_student: Optional[str] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None


class PetitionCreate(PetitionBase):
    pass

class PetitionRead(PetitionBase):
    id: uuid.UUID