from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from fastapi import UploadFile

from api.db.managers.student_document import StudentDocumentManager
from api.db.schema.student_documents import StudentDocuments
from api.pydantic_models.documents import StudentDocumentsCreate, StudentDocumentsUpdate
from api.handlers.exception_handler import ExceptionHandler


class StudentDocumentHandler:
    def __init__(self, db: Session):
        self.manager = StudentDocumentManager(db)
        self.exc = ExceptionHandler()

    async def create_document(self, employee_id: UUID) -> StudentDocuments:
        """
        Create a new document record with just the employee_id.
        """
        try:
            document_data = StudentDocumentsCreate(employee_id=employee_id)
            document = self.manager.create_document(document_data)  # Pass the correct object
            return document
        except Exception as e:
            raise self.exc.internal_error("creating the document", e)

    def get_document(self, document_id: UUID) -> StudentDocuments:
        document = self.manager.get_document(document_id)
        if not document:
            raise self.exc.not_found("Document", str(document_id))
        return document


    def get_documents_by_employee(self, employee_id: UUID) -> List[StudentDocuments]:
        """
        Retrieve all documents associated with a specific employee.
        """
        documents = self.manager.get_documents_by_employee(employee_id)
        if not documents:
            raise self.exc.not_found("Documents", message=f"No documents found for employee with ID {employee_id}")
        return documents

    def update_document(
        self, document_id: UUID, document_data: StudentDocumentsUpdate
    ) -> StudentDocuments:
        # Check if the document exists
        existing_document = self.manager.get_document(document_id)
        if not existing_document:
            raise self.exc.not_found("Document", str(document_id))

        # Proceed with the update
        document = self.manager.update_document(document_id, document_data)
        if not document:
            raise self.exc.update_failed("Document", str(document_id))
        return document

    def update_document_by_employee(
        self, employee_id: UUID, document_data: StudentDocumentsUpdate
    ) -> StudentDocuments:
        """
        Update a document by the foreign key of employee_id.
        """
        # Retrieve the document associated with the employee
        documents = self.manager.get_documents_by_employee(employee_id)
        if not documents:
            raise self.exc.not_found("Document", message=f"No document found for employee with ID {employee_id}")

        # Assuming there is only one document per employee, update the first document
        document = documents[0]

        # Proceed with the update
        updated_document = self.manager.update_document(document.id, document_data)
        if not updated_document:
            raise self.exc.update_failed("Document", message=f"Document for employee with ID {employee_id} could not be updated")
        return updated_document

    def delete_document(self, document_id: UUID) -> dict:
        # Check if the document exists
        existing_document = self.manager.get_document(document_id)
        if not existing_document:
            raise self.exc.not_found("Document", str(document_id))

        # Proceed with the deletion
        success = self.manager.delete_document(document_id)
        if not success:
            raise self.exc.delete_failed("Document", str(document_id))
        return {"detail": "Document deleted successfully"}

    async def save_file(self, file: UploadFile) -> str:
        """
        Save the uploaded file to a storage system and return the file path or URL.
        """
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        return file_location

    