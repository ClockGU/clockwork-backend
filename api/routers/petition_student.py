from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List
from uuid import UUID
from sqlmodel import Session

from api.handlers.document_handler import StudentDocumentHandler
from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import PetitionStudentUpdate, PetitionStudentRead
from api.db.dependencies import get_db
from api.security import get_current_supervisor, get_current_student, verify_signature

router = APIRouter()

## these are the api's fo petitions related to students

def get_document_handler(db: Session = Depends(get_db)) -> StudentDocumentHandler:
    return StudentDocumentHandler(db)

def get_petition_handler(
        db: Session = Depends(get_db)
        ) -> PetitionHandler:
    return PetitionHandler(db)

#Api to list all the petitions of students
@router.get("/students/petitions/", response_model=List[PetitionStudentRead])
def read_petitions(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_student)
):
    petitions = handler.get_student_petitions(user.get('email'))
    return petitions

@router.patch("/students/petitions/accept", response_model=PetitionStudentRead)
def update_petition_acceptance(
    acceptance_data: PetitionStudentUpdate,
    petition_id: UUID = Query(..., description="The ID of the petition to update"),
    signature: str = Query(..., description="Security signature for verification"),
    handler: PetitionHandler = Depends(get_petition_handler)
):
    """
    API for students to accept or reject their petition after receiving approval email.
    Accepts petition_id and signature as query parameters.
    Only allows status updates to 'rejected' or 'clerk_action'.
    """
    if not verify_signature(signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    handler.check_petition_exists(petition_id)
    
    updated_petition = handler.update_student_petition_status(
        petition_id=petition_id,
        status=acceptance_data.status
    )
    
    return updated_petition

@router.patch("/students/petitions/{petition_id}/student-action", response_model=PetitionStudentRead)
def student_accept_or_reject_petition(
    petition_id: UUID,
    action: PetitionStudentUpdate,
    handler: PetitionHandler = Depends(get_petition_handler)
):
    """
    API for students to accept or reject their petition.
    Only allowed if petition status is 'student_action'.
    """
    updated_petition = handler.student_accept_or_reject_petition(
        petition_id=petition_id,
        approved=action.approved
    )
    return updated_petition




