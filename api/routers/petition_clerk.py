from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session

from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import PetitionRead, PetitionClerkUpdate
from api.db.dependencies import get_db
from api.security import get_current_clerk

router = APIRouter()

# Dependency to get the petition handler
def get_petition_handler(
    db: Session = Depends(get_db)
) -> PetitionHandler:
    return PetitionHandler(db)

# 1. API to list all petitions with the status of "pending"
@router.get("/clerk/petitions/pending", response_model=List[PetitionRead])
def list_pending_petitions(
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)  
):
    petitions = handler.get_petitions_by_status("clerk_action")
    return petitions

# 2. API to delete a petition by ID
@router.delete("/clerk/petitions/{petition_id}")
def delete_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_clerk)
):
    success = handler.delete_petition(petition_id)
    return {"detail": "Petition deleted successfully"}

# 3. API to update a petition
@router.patch("/clerk/petitions/{petition_id}", response_model=PetitionRead)
def update_petition(
    petition_id: UUID,
    petition_data: PetitionClerkUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)  
):
    updated_petition = handler.update_petition_status_as_clerk(
        petition_id=petition_id,
        approved=petition_data.approved
    )
    return updated_petition

