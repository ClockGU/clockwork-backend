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
    budget_position_status: str 

class BudgetPositionApprovalUpdate(BaseModel):
    budget_position_status: str  
    message: Optional[str] = ""

    @field_validator("budget_position_status")
    def validate_budget_position_status(cls, status):
        # Validate that status is one of the allowed values
        allowed_statuses = ["approved", "rejected", "approver_revision", "waiting_approver_action"]
        if status not in allowed_statuses:
            raise ValueError(f"budget_position_status must be one of: {', '.join(allowed_statuses)}")
        return status