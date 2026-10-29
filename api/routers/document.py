import inspect
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import (
    get_document_for_clerk_or_owner,
    get_specified_petition,
)
from api.db.schema import Petition
from api.db.schema.student_documents import StudentDocuments
from api.handlers.document_handler import StudentDocumentHandler
from api.pydantic_models import StudentDocumentsRead, StudentDocumentsUpdate
from api.pydantic_models.documents import UPLOAD_FIELDS, DocumentType
from api.security import get_current_clerk, get_current_student
from api.utils import STUDENT_DOCUMENTS_DIR, file_response, save_student_doc_file

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


def files_dependency(names: list[str]):
    """
    Build a dependency that accepts an optional file upload for each name and returns
    only the files that were actually sent. Each name still shows up in Swagger.
    """

    def dep(**files: Optional[UploadFile]) -> dict[str, UploadFile]:
        return {k: v for k, v in files.items() if v is not None}

    dep.__signature__ = inspect.Signature(
        [
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Optional[UploadFile],
                default=File(None),
            )
            for name in names
        ]
    )
    return dep


UploadedFiles = Depends(files_dependency(UPLOAD_FIELDS))


@router.patch("/documents/{document_id}", response_model=StudentDocumentsRead)
def update_document(
    document_id: UUID,
    files: dict[str, UploadFile] = UploadedFiles,
    handler: StudentDocumentHandler = Depends(get_document_handler),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Update the caller's document. Save uploaded files and store their file names in the database.
    """
    if not files:
        raise HTTPException(status_code=422, detail="No files uploaded")

    document = handler.get_document_owned_by(document_id, user.get("sub"))

    file_names = {
        f"{name}_file": save_student_doc_file(document, name, file)
        for name, file in files.items()
    }

    return handler.update_document(document.id, StudentDocumentsUpdate(**file_names))


@router.get("/documents/{document_id}/{document_type}")
def download_document(
    document_type: DocumentType,
    document: StudentDocuments = Depends(get_document_for_clerk_or_owner),
    handler: StudentDocumentHandler = Depends(get_document_handler),
):
    """
    Download a file of a document. Only clerks and the owning student have access.
    """
    file_name = getattr(document, f"{document_type.value}_file")
    if not file_name:
        raise handler.exc.not_found(
            "File", message=f"No {document_type.value} file for document {document.id}"
        )
    return file_response(
        STUDENT_DOCUMENTS_DIR,
        file_name,
        f"{document_type.value}{Path(file_name).suffix}",
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
