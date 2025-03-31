from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import date

class Employee(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_account: uuid.UUID
    first_name: str
    last_name: str
    form_of_address: str
    gender: str
    date_of_birth: date
    city_of_birth: str
    address: str
    postal_code: str
    married: bool
    nationality: str
    telephone_number: str
    health_insurance: str
    previous_employment: Optional[str] = None
    prev_emp_duration: Optional[str] = None
    iban: str