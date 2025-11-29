from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from api.db.schema.student_documents import StudentDocuments
from api.db.schema.employee import Employee
from api.pydantic_models.documents import StudentDocumentsCreate, StudentDocumentsUpdate


class StudentDocumentManager:
    def __init__(self, db: Session):
        self.db = db
        self.schema = StudentDocuments  

    def create_document(self, document_data: StudentDocumentsCreate) -> StudentDocuments:
        """
        Create a new document record.
        """
        if isinstance(document_data, dict):
            # Handle plain dictionary
            document = self.schema(**document_data)
        else:
            # Handle Pydantic model
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

    def check_student_documents_uploaded(self, student_username: str) -> bool:
        """
        Check if a student has uploaded all required documents.
        
        Args:
            student_username: Username of the student
        
        Returns:
            bool: True if all documents are uploaded, False otherwise
        """
        
        # First get the employee by email
        employee_statement = select(Employee).where(Employee.username == student_username)
        employee_result = self.db.execute(employee_statement)
        employee = employee_result.scalar_one_or_none()
        
        # If employee doesn't exist, return False
        if not employee:
            return False
        
        # Get the student documents record using employee_id
        statement = select(self.schema).where(self.schema.employee_id == employee.id)
        result = self.db.execute(statement)
        student_docs = result.scalar_one_or_none()
        
        # If no document record exists, documents are not uploaded
        if not student_docs:
            return False
        
        # Check if all required document URLs are present and not empty
        required_documents = [
            student_docs.elstam_url,
            student_docs.studienbescheinigung_url,
            student_docs.versicherungsbescheinigung_url,
            student_docs.sozialversicherungsbogen_url
        ]
        
        # Return True only if all documents have non-empty URLs
        return all(doc_url and doc_url.strip() for doc_url in required_documents)

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

