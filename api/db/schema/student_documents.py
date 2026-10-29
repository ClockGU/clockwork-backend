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
    elstam_file: Optional[str] = None
    studienbescheinigung_file: Optional[str] = None
    versicherungsbescheinigung_file: Optional[str] = None
    sozialversicherungsbogen_file: Optional[str] = None
    ba_degree_file: Optional[str] = None
    residence_permit_file: Optional[str] = None
    id_photo_file: Optional[str] = None

    # Relationship to the Employee model
    employee: Optional["Employee"] = Relationship(back_populates="documents")
