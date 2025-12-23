from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class StudentDocumentsCreate(BaseModel):
    petition_id: UUID  # Required to associate the document with a petition
    studienbescheinigung_url: Optional[str] = None  # Accept URLs as strings
    versicherungsbescheinigung_url: Optional[str] = None  # Accept URLs as strings

class StudentDocumentsUpdate(BaseModel):
    elstam_url: Optional[str] = None  # Accept URLs as strings
    studienbescheinigung_url: Optional[str] = None  # Accept URLs as strings
    versicherungsbescheinigung_url: Optional[str] = None  # Accept URLs as strings
    sozialversicherungsbogen_url: Optional[str] = None  # Accept URLs as strings
    ba_degree_url: Optional[str] = None  # Accept URLs as strings

class StudentDocumentsRead(BaseModel):
    id: UUID
    employee_id: UUID
    elstam_url: Optional[str] = None
    studienbescheinigung_url: Optional[str] = None
    versicherungsbescheinigung_url: Optional[str] = None
    sozialversicherungsbogen_url: Optional[str] = None
    ba_degree_url: Optional[str] = None

    class Config:
        orm_mode = True

