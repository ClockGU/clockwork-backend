from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from api.db.schema.employee import Employee
from api.db.schema.student_documents import StudentDocuments
from api.pydantic_models.documents import StudentDocumentsUpdate


class StudentDocumentManager:
    def __init__(self, db: Session):
        self.db = db
        self.schema = StudentDocuments

    def get_or_create_document(self, document_data: dict) -> StudentDocuments:
        """
        Create a new document record.
        """

        document = self.schema(**document_data)

        try:
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            return document
        except IntegrityError:
            self.db.rollback()
            # If document already exists, we can safely ignore this error
            # as the employee already has a document associated
            return self.get_document_by_user_account(document_data["user_account"])

    def get_document(self, document_id: UUID) -> Optional[StudentDocuments]:
        """
        Retrieve a single document by its UUID.
        """
        return self.db.get(self.schema, document_id)

    def get_document_by_user_account(
        self, user_account: UUID
    ) -> Optional[StudentDocuments]:
        """
        Retrieve the document associated with a specific user account.
        """
        statement = select(self.schema).where(self.schema.user_account == user_account)
        result = self.db.execute(statement)
        return result.scalar_one_or_none()

    def check_student_documents_uploaded(
        self, employee: Employee, check_ba_degree: bool = False
    ) -> bool:
        """
        Check if a student has uploaded all required documents.

        Args:
            student_username: Username of the student
            check_ba_degree: Whether to check for BA degree upload

        Returns:
            bool: True if all documents are uploaded, False otherwise
        """

        # Get the student documents record using the employee's user_account
        student_docs = self.get_document_by_user_account(employee.user_account)

        # If no document record exists, documents are not uploaded
        if not student_docs:
            return False

        # Check if all required document URLs are present and not empty
        required_documents = [
            student_docs.elstam_file,
            student_docs.studienbescheinigung_file,
            student_docs.versicherungsbescheinigung_file,
            student_docs.sozialversicherungsbogen_file,
            student_docs.id_photo_file,
        ]

        if check_ba_degree:
            required_documents.append(student_docs.ba_degree_file)
        # TODO: Use global consts instead of magic string
        if employee.nationality and employee.nationality.lower() != "de":
            required_documents.append(student_docs.residence_permit_file)

        # Return True only if all documents have non-empty URLs
        return all(doc_url and doc_url.strip() for doc_url in required_documents)

    def update_document(
        self, document_id: UUID, document_data: StudentDocumentsUpdate
    ) -> Optional[StudentDocuments]:
        """
        Update an existing document record.
        """
        document = self.db.get(self.schema, document_id)
        if not document:
            return None

        # Update only the provided fields
        updated_data = document_data.dict(exclude_unset=True)
        for key, value in updated_data.items():
            setattr(document, key, value)

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete_document(self, document_id: UUID) -> bool:
        """
        Delete a document by its UUID.
        """
        document = self.db.get(self.schema, document_id)
        if not document:
            return False

        self.db.delete(document)
        self.db.commit()
        return True
