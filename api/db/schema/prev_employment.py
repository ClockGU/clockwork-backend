import uuid
from datetime import date
from typing import Optional

from sqlmodel import SQLModel, Field


class PrevEmployment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_account: uuid.UUID = Field(sa_column_kwargs={"unique": True})
    start: date
    end: date
    employer_name: Optional[str]
    proof: str
