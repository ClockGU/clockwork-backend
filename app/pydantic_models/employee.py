from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from uuid import UUID
from datetime import date


class EmployeeCreate(BaseModel):
    user_account: UUID  # Mandatory field for creation
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


class EmployeeUpdate(BaseModel):
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


class EmployeeRead(BaseModel):
    id: UUID
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

    class Config:
        orm_mode = True