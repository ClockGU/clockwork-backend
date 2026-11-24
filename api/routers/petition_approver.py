from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import get_specified_budget_position
from api.db.schema import BudgetPosition
from api.handlers.dependencies import get_petition_handler
from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import PetitionRead
from api.pydantic_models.budget_position import BudgetPositionApprovalUpdate
from api.security import verify_signature

router = APIRouter()


@router.get(
    "/approver/{budget_position_id}/{signature}",
    response_model=PetitionRead,
)
def read_petition(
    budget_position_id: UUID,
    signature: str,
    budget_position: BudgetPosition = Depends(get_specified_budget_position),
    db: Session = Depends(get_db)
):
    # TODO: This call is somehow unnecessarily complicated
    petition = PetitionHandler.from_existing_object(db, budget_position.petition).get_petition_for_approver_action(budget_position_id)
    return petition


@router.patch("/approver/{budget_position_id}/{signature}")
def update_budget_position_approval(
    budget_position_id: UUID,
    signature: str,
    approval_data: BudgetPositionApprovalUpdate = Body(...),
    budget_position: BudgetPosition = Depends(get_specified_budget_position),
    db: Session = Depends(get_db),
):
    """Update the approval status of a specific budget position"""
    # TODO: This call is somehow unnecessarily complicated
    updated_petition = PetitionHandler.from_existing_object(db, budget_position.petition).update_budget_position_approval(
        budget_position_id=budget_position_id,
        budget_position_approved=approval_data.budget_position_approved,
        message=approval_data.message,
        revision_requested=approval_data.revision_requested,
        subject=approval_data.subject,
    )

    return updated_petition
