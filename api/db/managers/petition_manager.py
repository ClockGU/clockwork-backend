from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from datetime import date

from api.consts import PetitionStatus
from api.db.schema.petition import Petition
from api.db.schema.budget_position import BudgetPosition
from api.pydantic_models import PetitionCreate, PetitionRead


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
                budget_position_approved=False,  # Default value
                percentage=budget_pos_data.percentage
            )
            self.db.add(budget_position)
        
        # Commit all changes
        self.db.commit()
        self.db.refresh(petition)
        return petition

    def get_petition(self, petition_id: UUID) -> Optional[Petition]:
        # Retrieve a single petition by its UUID with budget positions
        statement = (
            select(self.schema)
            .where(self.schema.id == petition_id)
            .options(selectinload(self.schema.budget_positions))
        )
        result = self.db.execute(statement)
        return result.scalar_one_or_none()

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

    def update_petition(self, petition_id: UUID, petition_data: dict) -> Optional[Petition]:
        # Find the petition first
        petition = self.db.get(self.schema, petition_id)
        if not petition:
            return None

        # Extract budget positions from update data
        budget_positions_data = petition_data.pop('budget_positions', None)
        
        # Update petition fields (excluding budget_positions)
        for key, value in petition_data.items():
            setattr(petition, key, value)

        # Handle budget positions update
        if budget_positions_data:
            # Delete existing budget positions
            self.db.execute(
                delete(BudgetPosition).where(BudgetPosition.petition_id == petition_id)
            )
            # Create new budget positions
            self.db.add_all(
                [BudgetPosition(
                petition_id=petition_id,
                **(budget_position | {"budget_position_approved": False})
            ) for budget_position in budget_positions_data]
            )

        self.db.add(petition)
        self.db.commit()
        self.db.refresh(petition)
        return petition

    def delete_petition(self, petition: Petition) -> bool:
        # Delete associated budget positions first (due to foreign key constraint)
        budget_positions = self.db.execute(
            select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
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
    
    def get_student_petitions(self, student_username: str) -> List[Petition]:
        # Retrieve all petitions for a student and check the status
        # TODO: Get rid of unnecessary statuses APPROVED, REJECTED, PENDING
        statement = select(self.schema).where(
            (self.schema.student_username == student_username) &
            (
            (self.schema.status != PetitionStatus.APPROVED) |
            (self.schema.status != PetitionStatus.REJECTED)
            )
        )
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
    
    def update_petition_status(self, petition: Petition, status: str) -> Petition:
        """Update petition status"""

        petition.status = status
        self.db.add(petition)
        self.db.commit()
        self.db.refresh(petition)
        
        # Load budget positions
        budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
        budget_result = self.db.execute(budget_statement)
        petition.budget_positions = budget_result.scalars().all()
        
        return petition
    
    def get_student_approved_petitions_in_semester(self, student_username: str, start_date: date) -> List[Petition]:
        """Get student's approved petitions in the same semester as the given start_date"""
        # Determine semester boundaries based on start_date
        year = start_date.year
        
        if start_date.month >= 4 and start_date.month <= 9:
            # Summer semester: April 1 - September 30
            semester_start = date(year, 4, 1)
            semester_end = date(year, 9, 30)
        else:
            # Winter semester: October 1 - March 31 (next year)
            if start_date.month >= 10:
                # October-December of current year
                semester_start = date(year, 10, 1)
                semester_end = date(year + 1, 3, 31)
            else:
                # January-March of current year (belongs to previous year's winter semester)
                semester_start = date(year - 1, 10, 1)
                semester_end = date(year, 3, 31)
        
        # Query petitions with student email, approved status, and overlapping dates with the semester
        statement = select(self.schema).where(
            (self.schema.student_username == student_username) &
            (self.schema.status == PetitionStatus.APPROVED) &
            (
            (self.schema.start_date >= semester_start) |
            (self.schema.end_date <= semester_end)  
            ) 
        )
        result = self.db.execute(statement)
        petitions = result.scalars().all()
        
        # Load budget positions for each petition
        for petition in petitions:
            budget_statement = select(BudgetPosition).where(BudgetPosition.petition_id == petition.id)
            budget_result = self.db.execute(budget_statement)
            petition.budget_positions = budget_result.scalars().all()
        
        return petitions



