import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import get_specified_petition
from api.db.schema import Petition
from api.handlers.document_handler import StudentDocumentHandler
from api.pydantic_models import StudentDocumentsRead, StudentDocumentsUpdate
from api.security import get_current_clerk, get_current_student
from api.utils import STUDENT_DOCUMENTS_DIR, save_student_doc_file, upload_file_path

router = APIRouter()


# Dependency to get the document handler
def get_document_handler(db: Session = Depends(get_db)) -> StudentDocumentHandler:
    return StudentDocumentHandler(db)


@router.get("/documents", response_model=StudentDocumentsRead)
def get_document(
    handler: StudentDocumentHandler = Depends(get_document_handler),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Retrieve a document by the user's account.
    """
    return handler.get_document_by_user_account(user.get("sub"))


@router.patch("/documents")
def update_document(
    elstam: Optional[UploadFile] = File(None),
    studienbescheinigung: Optional[UploadFile] = File(None),
    versicherungsbescheinigung: Optional[UploadFile] = File(None),
    sozialversicherungsbogen: Optional[UploadFile] = File(None),
    ba_degree: Optional[UploadFile] = File(None),
    residence_permit: Optional[UploadFile] = File(None),
    id_photo: Optional[UploadFile] = File(None),
    handler: StudentDocumentHandler = Depends(get_document_handler),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Update a document by the user's account. Save uploaded files and update their URLs in the database.
    """
    # Check if the document exists
    document = handler.get_document_by_user_account(user.get("sub"))

    # Save files and generate URLs
    # TODO: Make this dynamic to avoid repetition
    file_urls = {}
    if elstam:
        file_urls["elstam_file"] = save_student_doc_file(document, "elstam", elstam)
    if studienbescheinigung:
        file_urls["studienbescheinigung_file"] = save_student_doc_file(
            document, "studienbescheinigung", studienbescheinigung
        )
    if versicherungsbescheinigung:
        file_urls["versicherungsbescheinigung_file"] = save_student_doc_file(
            document, "versicherungsbescheinigung", versicherungsbescheinigung
        )
    if sozialversicherungsbogen:
        file_urls["sozialversicherungsbogen_file"] = save_student_doc_file(
            document, "sozialversicherungsbogen", sozialversicherungsbogen
        )
    if ba_degree:
        file_urls["ba_degree_file"] = save_student_doc_file(
            document, "ba_degree", ba_degree
        )
    if residence_permit:
        file_urls["residence_permit_file"] = save_student_doc_file(
            document, "residence_permit", residence_permit
        )
    if id_photo:
        file_urls["id_photo_file"] = save_student_doc_file(
            document, "id_photo", id_photo
        )

    document_data = StudentDocumentsUpdate(**file_urls)

    updated_document = handler.update_document(document.id, document_data)

    return updated_document


# TODO: THIS IS A NO-GO. This basically exposes the entire services filesystem to the outside world.
# Solution: /download-file/{student_document_id}/{document_type} and then check if the student_document_id
# belongs to the user and if the document_type is valid. Then return the file.
@router.get("/download-file")
def download_file(
    file_url: str = Query(..., description="The URL of the file to download")
):
    """
    Takes the URL of a file and returns the actual file.
    """
    upload_path = upload_file_path(STUDENT_DOCUMENTS_DIR, file_url)
    if not upload_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Return the file as a response
    return FileResponse(
        upload_path,
        media_type="application/octet-stream",
        filename=file_url,
    )


@router.get("/clerk/petitions/{petition_id}/documents", response_model=StudentDocumentsRead)
def get_petition_documents(
    petition_id: UUID,
    petition: Petition = Depends(get_specified_petition),
    handler: StudentDocumentHandler = Depends(get_document_handler),
    user=Depends(get_current_clerk),  # Secure the endpoint
):
    """
    Retrieve the student documents for a petition.
    """
    return handler.get_documents_for_petition(petition)
