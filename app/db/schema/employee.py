from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
import uuid
from datetime import date
from app.db.schema.student_documents import StudentDocuments  # Import the related model

class Employee(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_account: uuid.UUID  # Required field
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    form_of_address: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    city_of_birth: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    married: Optional[bool] = None
    nationality: Optional[str] = None
    telephone_number: Optional[str] = None
    health_insurance: Optional[str] = None
    previous_employment: Optional[str] = None
    prev_emp_duration: Optional[str] = None
    iban: Optional[str] = None

    # Add the documents relationship
    documents: List[StudentDocuments] = Relationship(back_populates="employee")