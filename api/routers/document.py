import inspect
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
from api.pydantic_models.documents import UPLOAD_FIELDS
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
