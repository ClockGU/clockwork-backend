from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlmodel import Session

from api.db.managers import PetitionManager
from api.db.managers.emploeyee_manager import (  # Note the typo in filename
    EmployeeManager,
)
from api.db.managers.student_document import StudentDocumentManager
from api.db.schema import Employee
from api.db.schema.student_documents import StudentDocuments
from api.handlers.email_handler import EmailHandler
from api.handlers.exception_handler import ExceptionHandler
from api.pydantic_models.documents import StudentDocumentsUpdate


class StudentDocumentHandler:
    def __init__(self, db: Session):
        self.manager = StudentDocumentManager(db)
        self.petition_manager = PetitionManager(db)
        self.employee_manager = EmployeeManager(db)
        self.exc = ExceptionHandler()

    def get_documents_by_student_username(
        self, student_username: str
    ) -> StudentDocuments:
        """
        Retrieve student documents by the student's username.
        """
        # 1. Fetch Student Employee
        student_employee = self.employee_manager.get_employee_by_username(
            student_username
        )
        if not student_employee:
            raise self.exc.not_found(
                "Student Employee", f"Student employee {student_username} not found"
            )

        # 2. Fetch Documents
        document = self.manager.get_document_by_user_account(
            student_employee.user_account
        )
        if not document:
            raise self.exc.not_found(
                "Documents", f"No documents found for student {student_username}"
            )

        return document

    def create_document(self, employee: Employee) -> StudentDocuments:
        """
        Create a new document record with just the user_account.
        """
        try:
            document = self.manager.get_or_create_document(
                {"user_account": employee.user_account}
            )
            return document
        except Exception as e:
            raise self.exc.internal_error("creating the document", e)

    def get_document(self, document_id: UUID) -> StudentDocuments:
        document = self.manager.get_document(document_id)
        if not document:
            raise self.exc.not_found("Document", str(document_id))
        return document

    def get_document_by_user_account(self, user_account: UUID) -> StudentDocuments:
        """
        Retrieve the document associated with a specific user account.
        """
        document = self.manager.get_document_by_user_account(user_account)
        if not document:
            raise self.exc.not_found(
                "Documents",
                message=f"No documents found for user account {user_account}",
            )
        return document

    def update_document(
        self, document_id: UUID, document_data: StudentDocumentsUpdate
    ) -> StudentDocuments:
        existing_document = self.manager.get_document(document_id)
        if not existing_document:
            raise self.exc.not_found("Document", str(document_id))

        document = self.manager.update_document(document_id, document_data)
        if not document:
            raise self.exc.update_failed("Document", str(document_id))

        return document

    def update_document_by_user_account(
        self, user_account: UUID, document_data: StudentDocumentsUpdate
    ) -> StudentDocuments:
        """
        Update a document by the foreign key of user_account.
        """
        # Retrieve the document associated with the user account
        document = self.manager.get_document_by_user_account(user_account)
        if not document:
            raise self.exc.not_found(
                "Document",
                message=f"No document found for user account {user_account}",
            )

        # Proceed with the update
        updated_document = self.manager.update_document(document.id, document_data)
        if not updated_document:
            raise self.exc.update_failed(
                "Document",
                message=f"Document for user account {user_account} could not be updated",
            )
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
