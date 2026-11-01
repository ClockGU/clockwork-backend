from typing import List

from pydantic import BaseModel

from .budget_position import BudgetPositionCreate
from .petition import PetitionBase
from .validators.petition_validators import PetitionValidationMixin


class PetitionCreateBase(PetitionBase, PetitionValidationMixin):
    budget_positions: List[BudgetPositionCreate]


class PetitionCreate(PetitionCreateBase):
    """
    Pydantic model for creating a new petition.
    Inherits from PetitionCreateBase.
    """

    pass
