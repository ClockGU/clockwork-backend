from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from app.db.schema.petition import Petition
from app.pydantic_models.petition import PetitionCreate

class PetitionManager:
    def __init__(self, db: Session):
        self.db = db
        self.schema = Petition  # Reference to the Petition model

    def create_petition(self, petition_data: PetitionCreate) -> Petition:
        # Convert the validated Pydantic model to a DB model using model_validate
        petition = self.schema.model_validate(petition_data)
        self.db.add(petition)
        self.db.commit()
        self.db.refresh(petition)
        return petition

    def get_petition(self, petition_id: UUID) -> Optional[Petition]:
        # Retrieve a single petition by its UUID
        return self.db.get(self.schema, petition_id)

    def get_petitions(self, offset: int = 0, limit: int = 100) -> List[Petition]:
        # Use SQLModel's select with explicit session execution
        statement = select(self.schema).offset(offset).limit(limit)
        result = self.db.execute(statement)  # Changed exec to execute
        return result.scalars().all()

    def update_petition(self, petition_id: UUID, petition_data: PetitionCreate) -> Optional[Petition]:
        # Find the petition first
        petition = self.db.get(self.schema, petition_id)
        if not petition:
            return None

        # Update only the provided fields
        updated_data = petition_data.model_dump(exclude_unset=True)
        for key, value in updated_data.items():
            setattr(petition, key, value)

        self.db.add(petition)
        self.db.commit()
        self.db.refresh(petition)
        return petition

    def delete_petition(self, petition_id: UUID) -> bool:
        # Retrieve the petition to delete
        petition = self.db.get(self.schema, petition_id)
        if not petition:
            return False

        self.db.delete(petition)
        self.db.commit()
        return True
    
    def get_petitions_by_user(self, user_account: UUID) -> List[Petition]:
        # Retrieve all petitions associated with a user
        statement = select(self.schema).where(self.schema.user_account == user_account)
        result = self.db.execute(statement)
        return result.scalars().all()
    
    def get_student_petitions(self, student_mail: str) -> List[Petition]:
        # Retrieve all petitions associated with a student
        statement = select(self.schema).where(self.schema.student_mail == student_mail)
        result = self.db.execute(statement)
        return result.scalars().all()
    
    def get_petitions_by_status(self, status: str) -> List[Petition]:
        return self.db.query(Petition).filter(Petition.status == status).all()
    
    def get_petitions_by_budget_approver(self, budget_approver_email: str) -> List[Petition]:
        # Retrieve all petitions associated with a specific budget approver email
        statement = select(self.schema).where(self.schema.budget_approver == budget_approver_email)
        result = self.db.execute(statement)
        return result.scalars().all()

