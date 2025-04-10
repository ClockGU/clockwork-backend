from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import UUID


class StudentDocuments(SQLModel, table=True):
    id: Optional[UUID] = Field(default=None, primary_key=True)
    employee_id: UUID = Field(foreign_key="employee.id", nullable=False)

    # Document fields
    elstam_url: Optional[str] = None
    studienbescheinigung_url: Optional[str] = None
    versicherungsbescheinigung_url: Optional[str] = None

    # Relationship to the Employee model
    employee: Optional["Employee"] = Relationship(back_populates="documents")