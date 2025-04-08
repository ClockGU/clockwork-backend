from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.handlers.petition_handler import PetitionHandler
from app.pydantic_models import (
    PetitionSupervisorCreate,
    PetitionRead,
    PetitionSupervisorUpdate
)
from app.db.dependencies import get_db
from app.security import get_current_supervisor, get_current_student, get_current_clerk

router = APIRouter()

## these are the api's fo petitions related to supervisor


def get_petition_handler(
        db: Session = Depends(get_db)
        ) -> PetitionHandler:
    return PetitionHandler(db)

@router.post("/supervisor/petitions/", response_model=PetitionRead)
def create_petition(
    petition: PetitionSupervisorCreate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petition.user_account = user.get('sub')
    created_petition = handler.create_petition(petition)
    return created_petition

@router.get("/supervisor/petitions/user", response_model=List[PetitionRead])
def read_petitions_by_user(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_clerk)
):
    petitions = handler.get_petitions_by_user(user.get('sub'))
    return petitions

@router.get("/supervisor/petitions/", response_model=List[PetitionRead])
def read_petitions(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
): 
    petitions = handler.list_petitions()
    return petitions

@router.get("/supervisor/petitions/{petition_id}", response_model=PetitionRead)
def read_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petition = handler.get_petition(petition_id)
    return petition

@router.patch("/supervisor/petitions/{petition_id}", response_model=PetitionRead)
def update_petition(
    petition_id: UUID,
    petition: PetitionSupervisorUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    updated_petition = handler.update_petition(petition_id, petition)
    return updated_petition

@router.delete("/supervisor/petitions/{petition_id}")
def delete_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    success = handler.delete_petition(petition_id)
    return {"detail": "Petition deleted successfully"}


