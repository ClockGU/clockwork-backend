from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.handlers.petition_handler import PetitionHandler
from app.pydantic_models import PetitionRead, PetitionClerkUpdate
from app.db.dependencies import get_db
from app.security import get_current_approver

router = APIRouter()

# Dependency to get the petition handler
def get_petition_handler(
    db: Session = Depends(get_db)
) -> PetitionHandler:
    return PetitionHandler(db)

@router.get("/approver/petitions/", response_model=List[PetitionRead])
def get_petitions_by_budget_approver(
    handler: PetitionHandler = Depends(get_petition_handler),
    current_user: dict = Depends(get_current_approver)
):
    """
    Get all petitions for the current budget approver based on their email.

    Args:
        handler (PetitionHandler): The petition handler dependency.
        current_user (dict): The current user information.

    Returns:
        List[PetitionRead]: A list of petitions associated with the budget approver.
    """
    budget_approver_email = current_user.get("email")  # Extract the email of the current user
    if not budget_approver_email:
        raise HTTPException(status_code=400, detail="Invalid budget approver email")

    petitions = handler.get_petitions_by_budget_approver(budget_approver_email)
    return petitions

@router.patch("/approver/petitions/{petition_id}", response_model=PetitionRead)
def update_petition(
    petition_id: UUID,
    petition_data: PetitionClerkUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_approver)  
):
    updated_petition = handler.update_petition(petition_id, petition_data)
    return updated_petition
