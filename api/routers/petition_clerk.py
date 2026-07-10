from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from uuid import UUID
from sqlmodel import Session

from api.db.managers.dependencies import get_specified_petition
from api.db.schema import Petition
from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import (
    PetitionRead, 
    PetitionClerkUpdate, 
    ClerkRevisionRequest,
    ClerkDeletionRequest
    )
from api.db.dependencies import get_db
from api.pydantic_models.dependencies import get_clerk_petition_update_model
from api.security import get_current_clerk
from api.consts import PetitionStatus
from api.websockets.routers.web_socket import send_serialized_data_to_clerks

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
    petition: Petition = Depends(get_specified_petition),
    deletion_request: ClerkDeletionRequest = Body(default=ClerkDeletionRequest(reason="")),
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_clerk)
):
    success = handler.delete_petition_as_clerk(petition, deletion_request.reason)
    await send_serialized_data_to_clerks([petition.dict(by_alias=True, exclude_none=True) for petition in handler.get_petitions_clerk()])
    return success

# 3. API to update a petition
@router.patch("/clerk/petitions/{petition_id}", response_model=PetitionRead)
async def update_petition_as_clerk(
    petition: Petition = Depends(get_specified_petition),
    petition_data: PetitionClerkUpdate = Depends(get_clerk_petition_update_model),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)  
):
    updated_petition = handler.update_petition_as_clerk(
        petition=petition,
        approved=petition_data.approved
    )
    if updated_petition.status == 'rejected':
        return handler.delete_petition(petition)
   
   
    return updated_petition

@router.patch("/clerk/petitions/{petition_id}/request-revision", response_model=PetitionRead)
async def request_revision_from_student(
    petition: Petition = Depends(get_specified_petition),
    revision: ClerkRevisionRequest = Body(...),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk)
):
    updated_petition = handler.request_revision_from_student(
        petition=petition,
        message=revision.message,
        subject=revision.subject
    )
    return updated_petition