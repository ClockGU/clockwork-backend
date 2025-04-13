from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from fastapi import HTTPException

from app.db.managers import PetitionManager
from app.pydantic_models.petition import PetitionCreate  # Pydantic model for input
from app.db.schema.petition import Petition  # ORM model


class PetitionHandler:
    def __init__(self, db: Session):
        self.manager = PetitionManager(db)

    def create_petition(self, petition_data: PetitionCreate) -> Petition:
        try:
            petition = self.manager.create_petition(petition_data)
            if not petition:
                raise HTTPException(status_code=400, detail="Petition could not be created")
            return petition
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while creating the petition: {str(e)}")

    def list_petitions(self, offset: int = 0, limit: int = 100) -> List[Petition]:
        petitions = self.manager.get_petitions(offset=offset, limit=limit)
        if not petitions:
            raise HTTPException(status_code=404, detail="No petitions found")
        return petitions

    def get_petition(self, petition_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        return petition

    def update_petition(self, petition_id: UUID, petition_data: PetitionCreate) -> Petition:
        # Check if the petition exists
        existing_petition = self.manager.get_petition(petition_id)
        if not existing_petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")

        # Proceed with the update
        petition = self.manager.update_petition(petition_id, petition_data)
        if not petition:
            raise HTTPException(status_code=400, detail=f"Petition with ID {petition_id} could not be updated")
        return petition

    def delete_petition(self, petition_id: UUID) -> dict:
        # Check if the petition exists
        existing_petition = self.manager.get_petition(petition_id)
        if not existing_petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")

        # Proceed with the deletion
        success = self.manager.delete_petition(petition_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Petition with ID {petition_id} could not be deleted")
        return {"detail": "Petition deleted successfully"}

    def get_petitions_by_user(self, user_account: UUID) -> List[Petition]:
        petitions = self.manager.get_petitions_by_user(user_account)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found for user with ID {user_account}")
        return petitions

    def get_student_petitions(self, student_mail: str) -> List[Petition]:
        petitions = self.manager.get_student_petitions(student_mail)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found for student with email {student_mail}")
        return petitions

    def get_petitions_by_status(self, status: str) -> List[Petition]:
        petitions = self.manager.get_petitions_by_status(status)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found with status '{status}'")
        return petitions
    
    def check_petition_exists(self, petition_id: UUID) -> None:
        # Check if the petition exists
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        