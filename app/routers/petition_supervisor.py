# app/routers/petition_router.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.handlers.petition_handler import PetitionHandler
from app.pydantic_models.petition import PetitionCreate, PetitionRead
from app.db.dependencies import get_db
from app.security import get_current_supervisor, get_current_student

router = APIRouter()

## these are the api's fo petitions related to supervisor


def get_petition_handler(
        db: Session = Depends(get_db)
        ) -> PetitionHandler:
    return PetitionHandler(db)

@router.post("/petitions/", response_model=PetitionRead)
def create_petition(
    petition: PetitionCreate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petition.user_account = user.get('sub')
    created_petition = handler.create_petition(petition)
    return created_petition

@router.get("/petitions/user", response_model=List[PetitionRead])
def read_petitions_by_user(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petitions = handler.get_petitions_by_user(user.get('sub'))
    return petitions

@router.get("/petitions/", response_model=List[PetitionRead])
def read_petitions(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petitions = handler.list_petitions()
    return petitions

@router.get("/petitions/{petition_id}", response_model=PetitionRead)
def read_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petition = handler.get_petition(petition_id)
    if not petition:
        raise HTTPException(status_code=404, detail="Petition not found")
    return petition

@router.put("/petitions/{petition_id}", response_model=PetitionRead)
def update_petition(
    petition_id: UUID,
    petition: PetitionCreate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    updated_petition = handler.update_petition(petition_id, petition)
    if not updated_petition:
        raise HTTPException(status_code=404, detail="Petition not found")
    return updated_petition

@router.delete("/petitions/{petition_id}")
def delete_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    success = handler.delete_petition(petition_id)
    if not success:
        raise HTTPException(status_code=404, detail="Petition not found")
    return {"detail": "Petition deleted successfully"}


