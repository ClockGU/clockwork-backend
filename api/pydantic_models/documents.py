from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from api.db.schema.student_documents import StudentDocuments

UPLOAD_FIELDS = [
    k.removesuffix("_file") for k in StudentDocuments.model_fields if k.endswith("_file")
]


class StudentDocumentsUpdate(BaseModel):
    elstam_file: Optional[str] = None
    studienbescheinigung_file: Optional[str] = None
    versicherungsbescheinigung_file: Optional[str] = None
    sozialversicherungsbogen_file: Optional[str] = None
    ba_degree_file: Optional[str] = None
    residence_permit_file: Optional[str] = None
    id_photo_file: Optional[str] = None


class StudentDocumentsRead(BaseModel):
    id: UUID
    user_account: UUID
    elstam_file: Optional[str] = None
    studienbescheinigung_file: Optional[str] = None
    versicherungsbescheinigung_file: Optional[str] = None
    sozialversicherungsbogen_file: Optional[str] = None
    ba_degree_file: Optional[str] = None
    residence_permit_file: Optional[str] = None
    id_photo_file: Optional[str] = None

    class Config:
        orm_mode = True
