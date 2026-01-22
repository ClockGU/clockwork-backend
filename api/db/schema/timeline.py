from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from datetime import datetime
from typing import Dict, Any

class PetitionTimeline(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Using sa_column to ensure ondelete CASCADE works at DB level
    petition_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True), 
            ForeignKey("petition.id", ondelete="CASCADE"), 
            unique=True,
            index=True,
            nullable=False
        )
    )
    
    # Stores { "logs": [...], "notifications": {...} }
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    last_updated_at: datetime = Field(default_factory=datetime.now, index=True)
