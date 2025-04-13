from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
from uuid import UUID
from sqlmodel import Session
import os
import uuid

from app.handlers.document_handler import StudentDocumentHandler
from app.handlers.employee_handler import EmployeeHandler
from app.pydantic_models import StudentDocumentsUpdate, StudentDocumentsRead
from app.db.dependencies import get_db
from app.security import get_current_student

router = APIRouter()

# Dependency to get the document handler
def get_document_handler(db: Session = Depends(get_db)) -> StudentDocumentHandler:
    return StudentDocumentHandler(db)


@router.get("/documents/", response_model=StudentDocumentsRead)
def get_document(
    handler: StudentDocumentHandler = Depends(get_document_handler),
    employee_handler: EmployeeHandler = Depends(lambda db=Depends(get_db): EmployeeHandler(db)),
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


@router.patch("/documents/")
def update_document(
    elstam: Optional[UploadFile] = File(None),
    studienbescheinigung: Optional[UploadFile] = File(None),
    versicherungsbescheinigung: Optional[UploadFile] = File(None),
    handler: StudentDocumentHandler = Depends(get_document_handler),
    employee_handler: EmployeeHandler = Depends(lambda db=Depends(get_db): EmployeeHandler(db)),
    user=Depends(get_current_student),  # Secure the endpoint
):
    """
    Update a document by the user's associated employee ID. Save uploaded files and update their URLs in the database.
    """
    # Define the root directory as the parent directory of the 'routers' folder
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Go one level up to the 'app' directory
    upload_dir = os.path.join(root_dir, "uploads")  # Create the uploads folder in the root directory
    os.makedirs(upload_dir, exist_ok=True)  # Create the folder if it doesn't exist

    # Get the employee associated with the user
    employee = employee_handler.get_employee_by_user_account(user.get("sub"))

    # Check if the document exists
    documents = handler.get_documents_by_employee(employee.id)

    # Assuming there is only one document per employee
    document = documents[0]

    # Save files and generate URLs
    file_urls = {}
    if elstam:
        file_urls["elstam_url"] = save_file(elstam, upload_dir)  
    if studienbescheinigung:
        file_urls["studienbescheinigung_url"] = save_file(studienbescheinigung, upload_dir)  
    if versicherungsbescheinigung:
        file_urls["versicherungsbescheinigung_url"] = save_file(versicherungsbescheinigung, upload_dir)  

    document_data = StudentDocumentsUpdate(**file_urls)  

    updated_document = handler.update_document(document.id, document_data)
    return updated_document


def save_file(file: UploadFile, upload_dir: str) -> str:
    """
    Save the uploaded file to the specified directory and return the file URL.
    """
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path