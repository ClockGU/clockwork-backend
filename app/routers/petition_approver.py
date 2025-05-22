from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.handlers.petition_handler import PetitionHandler
from app.handlers.email_handler import EmailHandler
from app.pydantic_models import PetitionRead, PetitionApproverUpdate
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


@router.patch("/approver/petitions/{petition_id}/{signature}", response_model=PetitionRead)
def update_petition(
    petition_id: UUID,
    signature: str,
    petition_data: PetitionApproverUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
):
    if not verify_signature(signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    if not hasattr(petition_data, "status") or petition_data.status is None:
        petition_data.status = "student_action" if petition_data.budget_approved else "rejected"

    updated_petition = handler.update_petition(petition_id, petition_data)

    if updated_petition.budget_approved:
        # Send email to supervisor
        email_handler = EmailHandler()
        email_handler.send_email(
            recipient=updated_petition.supervisor_mail,
            subject="Petition Approved", 
            body=f"Petition {updated_petition.id} has been approved."
        )
        # Send email to the student
        email_handler.send_email(
            recipient=updated_petition.student_mail,
            subject="Upload Documents", 
            body=f"Please upload the documents for your petition."
        )

    elif not updated_petition.budget_approved:
        handler.delete_petition(petition_id)
        # Send email to supervisor that it has been rejected
        email_handler = EmailHandler()
        email_handler.send_email(
            recipient=updated_petition.supervisor_mail,
            subject="Petition Rejected", 
            body=f"Petition {updated_petition.id} has been rejected by the approver and hence deleted."
        )

    return updated_petition
