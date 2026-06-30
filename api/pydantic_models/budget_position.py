from typing import Optional
import uuid
from pydantic import BaseModel
from .validators.budget_position_validators import BudgetPositionValidationMixin
from sqlmodel import SQLModel


class BudgetPositionBase(SQLModel):
    budget_position: str
    budget_approver: str
    percentage: float
    budget_position_approved: bool

class BudgetPositionCreate(BudgetPositionBase, BudgetPositionValidationMixin):
    pass

class BudgetPositionRead(BudgetPositionBase):
    id: uuid.UUID


class BudgetPositionApprovalUpdate(BaseModel):
    budget_position_approved: bool
    message: Optional[str] = ""
    revision_requested: bool = False
    subject: Optional[str] = None

    