from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import get_specified_petition
from api.db.schema import Petition
from api.handlers.dependencies import get_petition_handler
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


# Api to list all the petitions of students
@router.get("/students/petitions", response_model=List[PetitionStudentRead])
def read_petitions(
    petition: Depends(get_specified_petition),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_student),
):
    petitions = handler.get_student_petitions(user.get("username"))
    return petitions


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


# TODO:Should be a POST endpoint
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

    updated_petition = handler.request_revision_from_supervisor(
        petition, revision_data.message, revision_data.subject
    )
    return updated_petition
