from typing import List

from pydantic import BaseModel

from .budget_position import BudgetPositionCreate
from .petition import PetitionBase
from .validators.petition_validators import PetitionValidationMixin


class PetitionCreateBase(PetitionBase, PetitionValidationMixin):
    budget_positions: List[BudgetPositionCreate]


class PetitionSupervisorCreate(PetitionCreateBase):
    """
    Pydantic model for creating a new petition.
    Inherits from PetitionCreateBase.
    """

    pass


class PetitionStudentAction(BaseModel):
    approved: bool


class PetitionCreate(PetitionCreateBase):
    """
    Pydantic model for creating a new petition.
    Inherits from PetitionCreateBase.
    """

    pass
