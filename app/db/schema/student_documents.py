from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
import uuid

class StudentDocuments(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    employee_id: uuid.UUID = Field(foreign_key="employee.id", nullable=False)

    # Document fields
    elstam_url: Optional[str] = None
    studienbescheinigung_url: Optional[str] = None
    versicherungsbescheinigung_url: Optional[str] = None

    # Relationship to the Employee model
    employee: Optional["Employee"] = Relationship(back_populates="documents")