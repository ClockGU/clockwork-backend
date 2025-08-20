from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
import uuid

class BudgetPosition(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    petition_id: uuid.UUID = Field(foreign_key="petition.id", nullable=False)
    budget_position: str = Field(nullable=False)
    budget_approver: str = Field(nullable=False)
    budget_position_status: str = Field(default="waiting approver action", nullable=True)
    # Possible values: "approved", "rejected", "approver revision", "waiting approver action"
    percentage: Optional[float] = Field(default=0, nullable=True)  # Made nullable
    
    # Relationship back to petition
    petition: "Petition" = Relationship(back_populates="budget_positions")