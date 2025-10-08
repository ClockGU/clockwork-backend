from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.handlers.petition_handler import PetitionHandler
from app.pydantic_models import (
    PetitionRead, 
    PetitionClerkUpdate, 
    ClerkRevisionRequest
    )
from app.db.dependencies import get_db
from app.security import get_current_clerk

router = APIRouter()

# Dependency to get the petition handler
def get_petition_handler(
    db: Session = Depends(get_db)
) -> PetitionHandler:
    return PetitionHandler(db)

# 1. API to list all petitions with the status of "pending"
@router.get("/clerk/petitions", response_model=List[PetitionRead])
def list_petitions_by_status(
    status: str = Depends(lambda status: status),  # For OpenAPI docs, use Query instead
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)
):
    allowed_statuses = {"clerk_action", "awaiting_signature", "completed", "clerk_revision"}# this is temprorary will change later
    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {allowed_statuses}")
    petitions = handler.get_petitions_by_status(status)
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



@router.patch("/clerk/petitions/{petition_id}/request-revision", response_model=PetitionRead)
def request_revision_from_student(
    petition_id: UUID,
    revision: ClerkRevisionRequest = Body(...),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)
):
    updated_petition = handler.request_revision_from_student(
        petition_id=petition_id,
        message=revision.message
    )
    return updated_petition



