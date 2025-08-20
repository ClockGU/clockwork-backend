from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.handlers.petition_handler import PetitionHandler
from app.pydantic_models import PetitionRead
from app.pydantic_models.budget_position import BudgetPositionApprovalUpdate
from app.db.dependencies import get_db
from app.security import verify_signature

router = APIRouter()

# Dependency to get the petition handler
def get_petition_handler(
    db: Session = Depends(get_db)
) -> PetitionHandler:
    return PetitionHandler(db)

@router.get("/approver/petitions/{petition_id}", response_model=PetitionRead)
def read_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
):
    petition = handler.get_petition(petition_id)
    return petition


@router.patch("/approver/petitions/{petition_id}/{signature}/{budget_position_id}", response_model=PetitionRead)
def update_budget_position_approval(
    petition_id: UUID,
    signature: str,
    budget_position_id: UUID,
    approval_data: BudgetPositionApprovalUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
):
    """Update the approval status of a specific budget position"""
    if not verify_signature(signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    updated_petition = handler.update_budget_position_approval(
        petition_id=petition_id,
        budget_position_id=budget_position_id,
        budget_approved=approval_data.budget_approved
    )

    return updated_petition
