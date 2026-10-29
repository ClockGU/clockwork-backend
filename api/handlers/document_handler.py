from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlmodel import Session

from api.db.managers import PetitionManager
from api.db.managers.student_document import StudentDocumentManager
from api.db.schema import Employee, Petition
from api.db.schema.student_documents import StudentDocuments
from api.handlers.email_handler import EmailHandler
from api.handlers.exception_handler import ExceptionHandler
from api.pydantic_models.documents import StudentDocumentsUpdate


class StudentDocumentHandler:
    def __init__(self, db: Session):
        self.manager = StudentDocumentManager(db)
        self.petition_manager = PetitionManager(db)
        self.exc = ExceptionHandler()

    def get_documents_for_petition(self, petition: Petition) -> StudentDocuments:
        """
        Retrieve the student documents belonging to a petition's student.
        """
        # TODO: Use petition.user_account once it is stored on the petition (#142)
        document = self.manager.get_document_by_username(petition.student_username)
        if not document:
            raise self.exc.not_found(
                "Documents", f"No documents found for petition {petition.id}"
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

    def get_document_owned_by(
        self, document_id: UUID, user_account: UUID
    ) -> StudentDocuments:
        """
        Retrieve a document owned by the given user account. A document that exists
        but belongs to someone else is reported as not found.
        """
        document = self.manager.get_document_owned_by(document_id, user_account)
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
