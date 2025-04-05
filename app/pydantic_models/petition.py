
from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import date


class PetitionBase(SQLModel):
    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int
    ba_degree: bool  # Changed from str to bool
    budget_position: str
    budget_approver: str
    student_mail: str

    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None  # Ensure this is optional
    time_exce_end: Optional[date] = None  # Ensure this is optional

    duration_exce_course: Optional[bool] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None  # Ensure this is optional
    duration_exce_end: Optional[date] = None  # Ensure this is optional
# validations to be added
#1. start_date should be before end_date
#2. minutes should be greater than 0
#3. eos_number should be a valid format
#4. time_exc should be there as whole or not at all
#5. duration_exc should be there as whole or not at all

class PetitionCreate(PetitionBase):
    pass

class PetitionRead(PetitionBase):
    id: uuid.UUID

class PetitionStudentBase(SQLModel):
    start_date: date
    end_date: date
    minutes: int
    student_mail: str
    time_exce_student: Optional[str] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    duration_exce_student: Optional[str] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None

class PetitionStudentUpdate(PetitionStudentBase):
    pass
