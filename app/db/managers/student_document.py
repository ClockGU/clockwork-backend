from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from app.db.schema.student_documents import StudentDocuments
from app.pydantic_models.documents import StudentDocumentsCreate, StudentDocumentsUpdate


class StudentDocumentManager:
    def __init__(self, db: Session):
        self.db = db
        self.schema = StudentDocuments  

    def create_document(self, document_data: StudentDocumentsCreate) -> StudentDocuments:
        """
        Create a new document record.
        """
        document = self.schema(**document_data.dict())
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_document(self, document_id: UUID) -> Optional[StudentDocuments]:
        """
        Retrieve a single document by its UUID.
        """
        return self.db.get(self.schema, document_id)

    def get_documents_by_employee(self, employee_id: UUID) -> List[StudentDocuments]:
        """
        Retrieve all documents associated with a specific employee.
        """
        statement = select(self.schema).where(self.schema.employee_id == employee_id)
        result = self.db.execute(statement)
        return result.scalars().all()

    def update_document(self, document_id: UUID, document_data: StudentDocumentsUpdate) -> Optional[StudentDocuments]:
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