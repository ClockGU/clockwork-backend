from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from app.db.schema.petition import Petition
from app.db.schema.budget_position import BudgetPosition
from app.pydantic_models.petition import PetitionCreate

class PetitionManager:
    def __init__(self, db: Session):
        self.db = db
        self.schema = Petition  # Reference to the Petition model

    def create_petition(self, petition_data: PetitionCreate) -> Petition:
        # Extract budget positions from petition data
        budget_positions_data = petition_data.budget_positions
        
        # Create petition data without budget_positions
        petition_dict = petition_data.model_dump(exclude={'budget_positions'})
        petition = self.schema.model_validate(petition_dict)
        
        # Add and flush to get the petition ID
        self.db.add(petition)
        self.db.flush()  # This ensures petition.id is available
        
        # Create budget positions linked to this petition
        for budget_pos_data in budget_positions_data:
            budget_position = BudgetPosition(
                petition_id=petition.id,
                budget_position=budget_pos_data.budget_position,
                budget_approver=budget_pos_data.budget_approver,
                budget_approved=False  # Default value
            )
            self.db.add(budget_position)
        
        # Commit all changes
        self.db.commit()
        self.db.refresh(petition)
        return petition

    def get_petition(self, petition_id: UUID) -> Optional[Petition]:
        # Retrieve a single petition by its UUID with budget positions
        statement = select(self.schema).where(self.schema.id == petition_id)
        result = self.db.execute(statement)
        petition = result.scalar_one_or_none()
        
        if petition:
            # Load budget positions
            budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition_id)
            budget_result = self.db.execute(budget_statement)
            petition.budget_positions = budget_result.scalars().all()
        
        return petition

    def get_petitions(self, offset: int = 0, limit: int = 100) -> List[Petition]:
        # Use SQLModel's select with explicit session execution
        statement = select(self.schema).offset(offset).limit(limit)
        result = self.db.execute(statement)
        petitions = result.scalars().all()
        
        # Load budget positions for each petition
        for petition in petitions:
            budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
            budget_result = self.db.execute(budget_statement)
            petition.budget_positions = budget_result.scalars().all()
        
        return petitions

    def update_petition(self, petition_id: UUID, petition_data: PetitionCreate) -> Optional[Petition]:
        # Find the petition first
        petition = self.db.get(self.schema, petition_id)
        if not petition:
            return None

        # Extract budget positions from update data
        budget_positions_data = petition_data.budget_positions
        
        # Update petition fields (excluding budget_positions)
        updated_data = petition_data.model_dump(exclude_unset=True, exclude={'budget_positions'})
        for key, value in updated_data.items():
            setattr(petition, key, value)

        # Handle budget positions update
        if budget_positions_data:
            # Delete existing budget positions
            existing_budget_positions = self.db.execute(
                select(BudgetPosition).where(BudgetPosition.petition_id == petition_id)
            ).scalars().all()
            
            for existing_bp in existing_budget_positions:
                self.db.delete(existing_bp)
            
            # Create new budget positions
            for budget_pos_data in budget_positions_data:
                budget_position = BudgetPosition(
                    petition_id=petition.id,
                    budget_position=budget_pos_data.budget_position,
                    budget_approver=budget_pos_data.budget_approver,
                    budget_approved=False
                )
                self.db.add(budget_position)

        self.db.add(petition)
        self.db.commit()
        self.db.refresh(petition)
        return petition

    def delete_petition(self, petition_id: UUID) -> bool:
        # Retrieve the petition to delete
        petition = self.db.get(self.schema, petition_id)
        if not petition:
            return False

        # Delete associated budget positions first (due to foreign key constraint)
        budget_positions = self.db.execute(
            select(BudgetPosition).where(BudgetPosition.petition_id == petition_id)
        ).scalars().all()
        
        for budget_position in budget_positions:
            self.db.delete(budget_position)

        # Delete the petition
        self.db.delete(petition)
        self.db.commit()
        return True
    
    def get_petitions_by_user(self, user_account: UUID) -> List[Petition]:
        # Retrieve all petitions associated with a user
        statement = select(self.schema).where(self.schema.user_account == user_account)
        result = self.db.execute(statement)
        petitions = result.scalars().all()
        
        # Load budget positions for each petition
        for petition in petitions:
            budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
            budget_result = self.db.execute(budget_statement)
            petition.budget_positions = budget_result.scalars().all()
        
        return petitions
    
    def get_student_petitions(self, student_mail: str) -> List[Petition]:
        # Retrieve all petitions associated with a student
        statement = select(self.schema).where(self.schema.student_mail == student_mail)
        result = self.db.execute(statement)
        petitions = result.scalars().all()
        
        # Load budget positions for each petition
        for petition in petitions:
            budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
            budget_result = self.db.execute(budget_statement)
            petition.budget_positions = budget_result.scalars().all()
        
        return petitions
    
    def get_petitions_by_status(self, status: str) -> List[Petition]:
        statement = select(self.schema).where(self.schema.status == status)
        result = self.db.execute(statement)
        petitions = result.scalars().all()
        
        # Load budget positions for each petition
        for petition in petitions:
            budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
            budget_result = self.db.execute(budget_statement)
            petition.budget_positions = budget_result.scalars().all()
        
        return petitions
    
    def get_petitions_by_budget_approver(self, budget_approver_email: str) -> List[Petition]:
        # Query petitions through budget positions
        statement = (
            select(self.schema)
            .join(BudgetPosition, self.schema.id == BudgetPosition.petition_id)
            .where(BudgetPosition.budget_approver == budget_approver_email)
        )
        result = self.db.execute(statement)
        petitions = result.scalars().all()
        
        # Load budget positions for each petition
        for petition in petitions:
            budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
            budget_result = self.db.execute(budget_statement)
            petition.budget_positions = budget_result.scalars().all()
        
        return petitions

