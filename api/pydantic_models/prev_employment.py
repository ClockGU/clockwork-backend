import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel

class PrevEmploymentCreate(BaseModel):
    user_account: uuid.UUID
    start: date
    end: date
    employer_name: Optional[str] = None
