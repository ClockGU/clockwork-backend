from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import get_specified_petition
from api.db.schema import Petition
from api.handlers.document_handler import StudentDocumentHandler
from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import (
    PetitionStudentRead,
    PetitionStudentUpdate,
    StudenRevisionRequest,
)
from api.pydantic_models.dependencies import get_student_petition_update_model
from api.security import get_current_student, get_current_supervisor, verify_signature

router = APIRouter()

## these are the api's fo petitions related to students


def get_document_handler(db: Session = Depends(get_db)) -> StudentDocumentHandler:
    return StudentDocumentHandler(db)


def get_petition_handler(db: Session = Depends(get_db)) -> PetitionHandler:
    return PetitionHandler(db)


# Api to list all the petitions of students
@router.get("/students/petitions", response_model=List[PetitionStudentRead])
def read_petitions(
    petition: Depends(get_specified_petition),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_student),
):
    petitions = handler.get_student_petitions(user.get("username"))
    return petitions


# TODO: Endpoint is unused by frontend
@router.patch("/students/petitions/accept")
async def update_petition_acceptance(
    acceptance_data: PetitionStudentUpdate,
    petition_id: UUID = Query(..., description="The ID of the petition to update"),
    signature: str = Query(..., description="Security signature for verification"),
    handler: PetitionHandler = Depends(get_petition_handler),
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
        petition_id=petition_id, status=acceptance_data.status
    )
    if updated_petition.status == "rejected":
        updated_petition = handler.delete_petition(petition_id)

    return updated_petition


# TODO: Aproval/Rejection needs to be handled via centralized endpoint. Rejection is always a deletion patch masks that here
@router.patch("/students/petitions/{petition_id}/student-action")
async def student_accept_or_reject_petition(
    petition: Petition = Depends(get_specified_petition),
    petition_data: PetitionStudentUpdate = Depends(get_student_petition_update_model),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_student),
):
    """
    API for students to accept or reject their petition.
    Only allowed if petition status is 'student_action'.
    """
    updated_petition = handler.student_accept_or_reject_petition(
        petition=petition, approved=petition_data.approved
    )

    return updated_petition


@router.patch(
    "/students/petitions/{petition_id}/revision-done",
    response_model=PetitionStudentRead,
)
async def mark_revision_done(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_student),
):
    """
    API for students to mark their petition as revision done.
    """
    updated_petition = handler.mark_revision_done_student(petition_id)
    return updated_petition


@router.patch(
    "/students/petitions/{petition_id}/request-revision",
    response_model=PetitionStudentRead,
)
async def request_revision_from_supervisor(
    revision_data: StudenRevisionRequest,
    petition: Petition = Depends(get_specified_petition),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_student),
):
    """
    API for students to request revision from supervisor.
    Sends email to supervisor and changes petition status to 'student_revision'.
    Body: {"body": "revision message"}
    """
    if not revision_data.body:
        raise HTTPException(status_code=400, detail="Revision request text is required")

    updated_petition = handler.request_revision_from_supervisor(
        petition, revision_data.body, subject=revision_data.subject
    )
    return updated_petition
