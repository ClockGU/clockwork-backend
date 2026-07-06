from typing import Optional
from uuid import UUID
from sqlmodel import Session, select

from api.db.schema.budget_position import BudgetPosition

class BudgetPositionManager:
    def __init__(self, db: Session):
        self.db = db

    def get_budget_position(self, budget_position_id: UUID) -> Optional[BudgetPosition]:
        """Get a specific budget position by ID"""
        return self.db.get(BudgetPosition, budget_position_id)

    def update_budget_position_status(self, budget_position_id: UUID, budget_position_approved: bool) -> Optional[BudgetPosition]:
        """Update the approval status of a budget position"""
        budget_position = self.db.get(BudgetPosition, budget_position_id)
        if not budget_position:
            return None
        
        budget_position.budget_position_approved = budget_position_approved
        self.db.add(budget_position)
        self.db.commit()
        self.db.refresh(budget_position)
        return budget_position

    def check_all_budget_positions_approved(self, petition_id: UUID) -> bool:
        """Check if all budget positions for a petition are approved"""
        statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition_id)
        budget_positions = self.db.execute(statement).scalars().all()
        
        return all(bp.budget_position_approved for bp in budget_positions)

    def get_budget_positions_by_petition(self, petition: Petition) -> list[BudgetPosition]:
        """Get all budget positions for a petition"""
        statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
        return self.db.execute(statement).scalars().all()