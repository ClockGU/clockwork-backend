from typing import Optional
import uuid
from pydantic import field_validator
import re
from pydantic import BaseModel

class BudgetPositionCreate(BaseModel):
    budget_position: str
    budget_approver: str

    @field_validator("budget_approver")
    def validate_budget_approver(cls, budget_approver):
        # Ensure budget_approver is a valid email format
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", budget_approver):
            raise ValueError("budget_approver must be a valid email address")
        return budget_approver

class BudgetPositionRead(BaseModel):
    id: uuid.UUID
    budget_position: str
    budget_approver: str
    budget_approved: bool

class BudgetPositionApprovalUpdate(BaseModel):
    budget_approved: bool