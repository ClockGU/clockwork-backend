from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from uuid import UUID
from sqlmodel import Session

from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import PetitionRead
from api.pydantic_models.budget_position import BudgetPositionApprovalUpdate
from api.db.dependencies import get_db
from api.security import verify_signature

router = APIRouter()

# Dependency to get the petition handler
def get_petition_handler(
    db: Session = Depends(get_db)
) -> PetitionHandler:
    return PetitionHandler(db)

@router.get("/approver/petitions/{petition_id}/{signature}/{budget_position_id}", response_model=PetitionRead)
def read_petition(
    petition_id: UUID,
    signature: str,
    budget_position_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
):
    if not verify_signature(signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    petition = handler.get_petition_for_approver_action(petition_id, budget_position_id)
    return petition

@router.patch("/approver/petitions/{petition_id}/{signature}/{budget_position_id}")
def update_budget_position_approval(
    petition_id: UUID,
    signature: str,
    budget_position_id: UUID,
    approval_data: BudgetPositionApprovalUpdate = Body(...),  
    handler: PetitionHandler = Depends(get_petition_handler),
):
    """Update the approval status of a specific budget position"""
    if not verify_signature(signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    updated_petition = handler.update_budget_position_approval(
        petition_id=petition_id,
        budget_position_id=budget_position_id,
        budget_position_approved=approval_data.budget_position_approved,
        message=approval_data.message,
        revision_requested=approval_data.revision_requested,
        subject=approval_data.subject
    )

    return updated_petition

@router.patch("/test")
def test_patch(data: BudgetPositionApprovalUpdate = Body(...)):
    print(data)
    return data
