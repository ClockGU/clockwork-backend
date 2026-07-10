from typing import Optional
import uuid
from pydantic import BaseModel, field_validator
from .validators.budget_position_validators import BudgetPositionValidationMixin
from sqlmodel import SQLModel


class BudgetPositionBase(SQLModel):
    budget_position: str
    budget_approver: str
    percentage: float
    budget_position_approved: bool


class BudgetPositionCreate(BudgetPositionBase, BudgetPositionValidationMixin):
    budget_position: str
    budget_approver: str
    percentage: float


class BudgetPositionRead(BudgetPositionBase):
    id: uuid.UUID

# TODO: Check where this is used and if we need it.
class BudgetPositionApprovalUpdate(BaseModel):
    budget_position_approved: bool
    message: Optional[str] = ""
    revision_requested: bool = False
    subject: Optional[str] = None

    