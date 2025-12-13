from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid
from datetime import date

from api.consts import PetitionStatus

class Petition(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_account: uuid.UUID
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int
    ba_degree: bool
    student_username: str
    supervisor_mail: Optional[str] = None
    
    status: str = Field(default=PetitionStatus.APPROVER_ACTION, nullable=False)

    # Relationship to budget positions (one-to-many)
    budget_positions: List["BudgetPosition"] = Relationship(back_populates="petition")

    #optional fields
    time_exce_course: Optional[bool] = None
    time_exce_student: Optional[bool] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    time_exce_time: Optional[int] = None
    #optional fields
    duration_exce_course: Optional[bool] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None

    @property
    def student_mail(self):
        return f"{self.student_username}@stud.uni-frankfurt.de"
