from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from uuid import UUID
from sqlmodel import Session

from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import (
    PetitionRead, 
    PetitionClerkUpdate, 
    ClerkRevisionRequest,
    ClerkDeletionRequest
    )
from api.db.dependencies import get_db
from api.security import get_current_clerk
from api.consts import PetitionStatus

router = APIRouter()

# Dependency to get the petition handler
def get_petition_handler(
    db: Session = Depends(get_db)
) -> PetitionHandler:
    return PetitionHandler(db)

# 1. API to list all petitions with the status of "pending"
@router.get("/clerk/petitions", response_model=List[PetitionRead])
def list_petitions_by_status(
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)  
):
    petitions = handler.get_petitions_clerk()
    return petitions

# 2. API to delete a petition by ID
@router.delete("/clerk/petitions/{petition_id}")
async def delete_petition(
    petition_id: UUID,
    deletion_request: ClerkDeletionRequest = Body(default=ClerkDeletionRequest(reason="")),
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_clerk)
):
    success = handler.delete_petition_as_clerk(petition_id, deletion_request.reason)
    await send_data_to_clerks(handler.get_petitions_clerk())
    return success
# 3. API to update a petition
@router.patch("/clerk/petitions/{petition_id}")
async def update_petition_as_clerk(
    petition_id: UUID,
    petition_data: PetitionClerkUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)  
):
    updated_petition = handler.update_petition_as_clerk(
        petition_id=petition_id,
        approved=petition_data.approved
    )
    if updated_petition.status == 'rejected':
        updated_petition = handler.delete_petition(petition_id)
   
   
    return updated_petition

@router.patch("/clerk/petitions/{petition_id}/request-revision", response_model=PetitionRead)
async def request_revision_from_student(
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