from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class EmployeeValidate(BaseModel):
    first_name: str
    last_name: str
    user_email: str
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
    previously_employed: bool
    prev_emp_duration: str
    iban: str
    bic: str
    bank_name: str

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_email: Optional[str] = None
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
    previously_employed: Optional[bool] = None
    prev_emp_duration: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None


class EmployeeRead(BaseModel):
    id: UUID
    first_name: Optional[str] = None
    user_email: Optional[str] = None
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
    previously_employeed: Optional[bool] = None
    prev_emp_duration: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
