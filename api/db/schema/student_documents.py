import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, Relationship, SQLModel


class StudentDocuments(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_account: uuid.UUID = Field(
        sa_column=Column(
            Uuid,
            ForeignKey("employee.user_account", onupdate="CASCADE"),
            unique=True,
            nullable=False,
        )
    )

    # Document fields
    elstam_url: Optional[str] = None
    studienbescheinigung_url: Optional[str] = None
    versicherungsbescheinigung_url: Optional[str] = None
    sozialversicherungsbogen_url: Optional[str] = None
    ba_degree_url: Optional[str] = None
    residence_permit_url: Optional[str] = None
    id_photo_url: Optional[str] = None

    # Relationship to the Employee model
    employee: Optional["Employee"] = Relationship(back_populates="documents")
