from typing import List, Optional
from uuid import UUID
from sqlmodel import Session

from app.db.managers import PetitionManager
from app.pydantic_models.petition import PetitionCreate  # Pydantic model for input
from app.db.schema.petition import Petition  # ORM model

class PetitionHandler:
    def __init__(self, db: Session):
        self.manager = PetitionManager(db)

    def create_petition(self, petition_data: PetitionCreate) -> Petition:
        return self.manager.create_petition(petition_data)

    def list_petitions(self, offset: int = 0, limit: int = 100) -> List[Petition]:
        return self.manager.get_petitions(offset=offset, limit=limit)

    def get_petition(self, petition_id: UUID) -> Optional[Petition]:
        return self.manager.get_petition(petition_id)

    def update_petition(self, petition_id: UUID, petition_data: PetitionCreate) -> Optional[Petition]:
        return self.manager.update_petition(petition_id, petition_data)

    def delete_petition(self, petition_id: UUID) -> bool:
        return self.manager.delete_petition(petition_id)
