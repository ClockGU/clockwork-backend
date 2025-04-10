from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class StudentDocumentsCreate(BaseModel):
    petition_id: UUID  # Required to associate the document with a petition


class StudentDocumentsUpdate(BaseModel):
    pass  # No fields here since files will be handled separately


class StudentDocumentsRead(BaseModel):
    id: UUID
    employee_id: UUID
    elstam_url: Optional[str] = None
    studienbescheinigung_url: Optional[str] = None
    versicherungsbescheinigung_url: Optional[str] = None

    class Config:
        orm_mode = True

