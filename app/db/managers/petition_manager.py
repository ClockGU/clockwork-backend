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
        # Retrieve a list of petitions with pagination
        statement = select(self.schema).offset(offset).limit(limit)
        result = self.db.exec(statement)
        return result.all()

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
