from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from fastapi import HTTPException, UploadFile

from app.db.managers.student_document import StudentDocumentManager
from app.db.schema.student_documents import StudentDocuments
from app.pydantic_models.documents import StudentDocumentsCreate, StudentDocumentsUpdate


class StudentDocumentHandler:
    def __init__(self, db: Session):
        self.manager = StudentDocumentManager(db)

    async def create_document(
        self,
        petition_id: UUID,
        bachelors_degree: Optional[UploadFile] = None,
        id_card: Optional[UploadFile] = None,
        transcript: Optional[UploadFile] = None,
        other_document: Optional[UploadFile] = None,
    ) -> StudentDocuments:
        try:
            # Save files and generate file paths
            file_urls = {}
            if bachelors_degree:
                file_urls["bachelors_degree_url"] = await self.save_file(bachelors_degree)
            if id_card:
                file_urls["id_card_url"] = await self.save_file(id_card)
            if transcript:
                file_urls["transcript_url"] = await self.save_file(transcript)
            if other_document:
                file_urls["other_document_url"] = await self.save_file(other_document)

            # Create the document record
            document_data = StudentDocumentsCreate(petition_id=petition_id)
            document = self.manager.create_document(
                StudentDocuments(**document_data.dict(), **file_urls)
            )
            return document
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while creating the document: {str(e)}",
            )

    def get_document(self, document_id: UUID) -> StudentDocuments:
        document = self.manager.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=404, detail=f"Document with ID {document_id} not found"
            )
        return document


    def get_documents_by_employee(self, employee_id: UUID) -> List[StudentDocuments]:
        """
        Retrieve all documents associated with a specific employee.
        """
        documents = self.manager.get_documents_by_employee(employee_id)
        if not documents:
            raise HTTPException(
                status_code=404, detail=f"No documents found for employee with ID {employee_id}"
            )
        return documents

    def update_document(
        self, document_id: UUID, document_data: StudentDocumentsUpdate
    ) -> StudentDocuments:
        # Check if the document exists
        existing_document = self.manager.get_document(document_id)
        if not existing_document:
            raise HTTPException(
                status_code=404, detail=f"Document with ID {document_id} not found"
            )

        # Proceed with the update
        document = self.manager.update_document(document_id, document_data)
        if not document:
            raise HTTPException(
                status_code=400,
                detail=f"Document with ID {document_id} could not be updated",
            )
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
            raise HTTPException(
                status_code=404, detail=f"No document found for employee with ID {employee_id}"
            )

        # Assuming there is only one document per employee, update the first document
        document = documents[0]

        # Proceed with the update
        updated_document = self.manager.update_document(document.id, document_data)
        if not updated_document:
            raise HTTPException(
                status_code=400,
                detail=f"Document for employee with ID {employee_id} could not be updated",
            )
        return updated_document

    def delete_document(self, document_id: UUID) -> dict:
        # Check if the document exists
        existing_document = self.manager.get_document(document_id)
        if not existing_document:
            raise HTTPException(
                status_code=404, detail=f"Document with ID {document_id} not found"
            )

        # Proceed with the deletion
        success = self.manager.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Document with ID {document_id} could not be deleted",
            )
        return {"detail": "Document deleted successfully"}

    async def save_file(self, file: UploadFile) -> str:
        """
        Save the uploaded file to a storage system and return the file path or URL.
        """
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        return file_location