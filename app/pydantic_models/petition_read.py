from sqlmodel import SQLModel
from typing import Optional, Literal, List
from datetime import date
import uuid
from pydantic import field_validator, model_validator
import re
from .budget_position import BudgetPositionRead


# Base class for shared fields
class PetitionBaseRead(SQLModel):
    start_date: date
    end_date: date
    minutes: int
    student_mail: str
    supervisor_mail: Optional[str] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None


# PetitionReadBase for clerks/supervisors
class PetitionRead(PetitionBaseRead):
    id: uuid.UUID
    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    ba_degree: bool
    status: Literal["pending", "approved", "student_action", "rejected", "approver_action", "clerk_action"] = "pending"
    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    duration_exce_course: Optional[bool] = None
    
    # Budget positions as a list instead of single fields
    budget_positions: List[BudgetPositionRead]


class PetitionStudentRead(PetitionBaseRead):
    time_exce_student: Optional[bool] = None
    duration_exce_student: Optional[bool] = None
    
    budget_positions: List[BudgetPositionRead]



