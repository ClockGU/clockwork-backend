from sqlmodel import SQLModel
from typing import Optional, Literal, List
from datetime import date
import uuid
from pydantic import field_validator, model_validator
import re
from .budget_position import BudgetPositionRead


# Base class for shared fields
class PetitionBaseRead(SQLModel):
    id: uuid.UUID
    start_date: date
    end_date: date
    minutes: int
    student_username: str
    supervisor_mail: Optional[str] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    time_exce_time: Optional[int] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None
    time_exce_course: Optional[bool] = None  
    duration_exce_course: Optional[bool] = None 
    status: Literal["pending", "approved", "student_action", "rejected", "approver_action","approver_revision", "clerk_action", "awaiting_signature", "completed", "clerk_revision", "student_revision"] = "pending"


# PetitionReadBase for clerks/supervisors
class PetitionRead(PetitionBaseRead):
    id: uuid.UUID
    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    ba_degree: bool
    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None  
    duration_exce_course: Optional[bool] = None  
    duration_exce_student: Optional[bool] = None
    budget_positions: List[BudgetPositionRead]

    class Config:
        orm_mode = True
        from_attributes = True


class PetitionStudentRead(PetitionBaseRead):
    time_exce_student: Optional[bool] = None
    duration_exce_student: Optional[bool] = None
    
    budget_positions: List[BudgetPositionRead]



