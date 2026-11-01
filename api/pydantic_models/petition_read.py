import uuid
from typing import List, Optional

from .budget_position import BudgetPositionRead
from .petition import PetitionBase


# Base class for shared fields
class PetitionBaseRead(PetitionBase):
    id: uuid.UUID
    student_mail: str

    budget_positions: List[BudgetPositionRead]


# PetitionReadBase for clerks/supervisors
class PetitionRead(PetitionBaseRead):

    class Config:
        orm_mode = True
        from_attributes = True


class PetitionStudentRead(PetitionBaseRead):
    time_exce_student: Optional[bool] = None
    duration_exce_student: Optional[bool] = None
    ba_degree: Optional[bool] = None

    budget_positions: List[BudgetPositionRead]
