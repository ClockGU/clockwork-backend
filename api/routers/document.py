import os
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from api.db.dependencies import get_db
from api.handlers.document_handler import StudentDocumentHandler
from api.handlers.employee_handler import EmployeeHandler
from api.pydantic_models import StudentDocumentsRead, StudentDocumentsUpdate
from api.security import get_current_clerk, get_current_student
from api.utils import save_file

router = APIRouter()


# Dependency to get the document handler
def get_document_handler(db: Session = Depends(get_db)) -> StudentDocumentHandler:
    return StudentDocumentHandler(db)


@router.get("/documents", response_model=StudentDocumentsRead)
def get_document(
    handler: StudentDocumentHandler = Depends(get_document_handler),
    employee_handler: EmployeeHandler = Depends(
        lambda db=Depends(get_db): EmployeeHandler(db)
    ),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Retrieve a document by the user's associated employee ID.
    """
    # Get the employee associated with the user
    employee = employee_handler.get_employee_by_user_account(user.get("sub"))

    # Get the document associated with the employee
    documents = handler.get_documents_by_employee(employee.id)

    return documents[0]


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
    employee_handler: EmployeeHandler = Depends(
        lambda db=Depends(get_db): EmployeeHandler(db)
    ),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Update a document by the user's associated employee ID. Save uploaded files and update their URLs in the database.
    """
    # Get the employee associated with the user
    employee = employee_handler.get_employee_by_user_account(user.get("sub"))

    # Check if the document exists
    documents = handler.get_documents_by_employee(employee.id)

    # Assuming there is only one document per employee
    document = documents[0]

    # Save files and generate URLs
    # TODO: Make this dynamic to avoid repetition
    file_urls = {}
    if elstam:
        file_urls["elstam_url"] = save_file(elstam)
    if studienbescheinigung:
        file_urls["studienbescheinigung_url"] = save_file(
            studienbescheinigung
        )
    if versicherungsbescheinigung:
        file_urls["versicherungsbescheinigung_url"] = save_file(
            versicherungsbescheinigung
        )
    if sozialversicherungsbogen:
        file_urls["sozialversicherungsbogen_url"] = save_file(
            sozialversicherungsbogen
        )
    if ba_degree:
        file_urls["ba_degree_url"] = save_file(ba_degree)
    if residence_permit:
        file_urls["residence_permit_url"] = save_file(residence_permit)
    if id_photo:
        file_urls["id_photo_url"] = save_file(id_photo)

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
    # Check if the file exists at the given URL
    if not os.path.exists(file_url):
        raise HTTPException(status_code=404, detail="File not found")

    # Return the file as a response
    return FileResponse(
        file_url,
        media_type="application/octet-stream",
        filename=os.path.basename(file_url),
    )


@router.get("/clerk/documents-by-username", response_model=StudentDocumentsRead)
def get_documents_by_student_username(
    student_username: str = Query(..., description="The username of the student"),
    handler: StudentDocumentHandler = Depends(get_document_handler),
    user=Depends(get_current_clerk),  # Secure the endpoint
):
    """
    Retrieve documents by the student's username.
    """
    return handler.get_documents_by_student_username(student_username)
