import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PrevEmploymentCreate(BaseModel):
    user_account: uuid.UUID
    start: date
    end: date
    employer_name: Optional[str] = None

class PrevEmploymentRead(BaseModel):
    id: uuid.UUID
    user_account: uuid.UUID
    start: date
    end: date
    employer_name: Optional[str] = None
    proof: Optional[str] = None

class PrevEmploymentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: Optional[date] = None
    end: Optional[date] = None
    employer_name: Optional[str] = None