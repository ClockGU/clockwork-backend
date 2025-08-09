from typing import Optional
import uuid
from pydantic import BaseModel, field_validator
import re



class BudgetPositionCreate(BaseModel):
    budget_position: str
    budget_approver: str
    percentage: float  

    @field_validator("budget_approver")
    def validate_budget_approver(cls, budget_approver):
        # Ensure budget_approver is a valid email format
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", budget_approver):
            raise ValueError("budget_approver must be a valid email address")
        return budget_approver

    @field_validator("percentage")
    def validate_percentage(cls, percentage):
        if percentage <= 0 or percentage > 100:
            raise ValueError("percentage must be between 0 and 100")
        return percentage

class BudgetPositionRead(BaseModel):
    id: uuid.UUID
    budget_position: str
    budget_approver: str
    budget_approved: bool

class BudgetPositionApprovalUpdate(BaseModel):
    budget_approved: bool