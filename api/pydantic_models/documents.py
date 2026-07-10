from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class StudentDocumentsUpdate(BaseModel):
    elstam_url: Optional[str] = None  # Accept URLs as strings
    studienbescheinigung_url: Optional[str] = None  # Accept URLs as strings
    versicherungsbescheinigung_url: Optional[str] = None  # Accept URLs as strings
    sozialversicherungsbogen_url: Optional[str] = None  # Accept URLs as strings
    ba_degree_url: Optional[str] = None  # Accept URLs as strings
    residence_permit_url: Optional[str] = None
    id_photo_url: Optional[str] = None

class StudentDocumentsRead(BaseModel):
    id: UUID
    employee_id: UUID
    elstam_url: Optional[str] = None
    studienbescheinigung_url: Optional[str] = None
    versicherungsbescheinigung_url: Optional[str] = None
    sozialversicherungsbogen_url: Optional[str] = None
    ba_degree_url: Optional[str] = None
    residence_permit_url: Optional[str] = None
    id_photo_url: Optional[str] = None

    class Config:
        orm_mode = True

