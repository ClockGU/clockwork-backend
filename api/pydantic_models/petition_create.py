from sqlmodel import SQLModel
from typing import Optional, Literal, List
from datetime import date
import uuid
from pydantic import field_validator, model_validator, BaseModel
import re
from .budget_position import BudgetPositionCreate
from api.consts import LEGAL_REGULAR_WORKTIME, LEGAL_REGULAR_CONTRACT_LENGTH
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