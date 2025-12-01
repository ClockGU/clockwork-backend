from sqlmodel import SQLModel
from typing import Optional, Literal
from datetime import date
import uuid
from pydantic import field_validator, model_validator
import re

## these pydantic models are for the manager of the petition
class PetitionBase(SQLModel):
    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int
    ba_degree: bool
    budget_position: str
    budget_approver: str
    student_username: str

    status: Literal["pending", "approved", "rejected"] = "pending"

    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    time_exce_time: Optional[int] = None

    duration_exce_course: Optional[bool] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None

    @field_validator("end_date")
    def validate_dates(cls, end_date, info):
        start_date = info.data.get("start_date")
        if start_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        return end_date

    @field_validator("minutes")
    def validate_minutes(cls, minutes):
        if minutes <= 0:
            raise ValueError("minutes must be greater than 0")
        return minutes

    @field_validator("eos_number")
    def validate_eos_number(cls, eos_number):
        # Accept either 5 digits OR 'F' followed by 5 digits
        if not re.match(r"^(F\d{5}|\d{5})$", eos_number):
            raise ValueError("eos_number must be either 5 digits or start with 'F' followed by 5 digits (e.g., F12345 or 12345)")
        return eos_number

    @model_validator(mode="after")
    def validate_time_exc(cls, values):
        # Ensure all time_exc fields are either fully provided or all are None
        time_exc_fields = [
            # values.time_exce_start,
            # values.time_exce_end,
            values.time_exce_time,
            values.time_exce_name,
        ]
        provided = [field for field in time_exc_fields if field is not None]
        if len(provided) > 0 and len(provided) != len(time_exc_fields):
            raise ValueError("All time_exc fields must be provided together or not at all")
        return values

    @model_validator(mode="after")
    def validate_duration_exc(cls, values):
        # Ensure all duration_exc fields are either fully provided or all are None
        duration_exc_fields = [
            values.duration_exce_start,
            values.duration_exce_end,
            values.duration_exce_name,
        ]
        provided = [field for field in duration_exc_fields if field is not None]
        if len(provided) > 0 and len(provided) != len(duration_exc_fields):
            raise ValueError("All duration_exc fields must be provided together or not at all")
        return values

    @field_validator("student_username")
    def validate_student_username(cls, student_username):
        if student_username is None or student_username == "":
            raise ValueError("student_username is required")
        return student_username

class PetitionCreate(PetitionBase):
    pass

class PetitionRead(SQLModel):
    id: uuid.UUID
    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int
    ba_degree: bool
    budget_position: str
    budget_approver: str
    student_username: str

    status: Literal["pending", "approved", "student_action", "rejected", "approver_action","approver_revision", "clerk_action", "awaiting_signature", "completed", "clerk_revision"] = "pending"

    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None

    duration_exce_course: Optional[bool] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None

class PetitionStudentBase(SQLModel):
    start_date: date
    end_date: date
    minutes: int
    student_username: str
    time_exce_student: Optional[str] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None
    duration_exce_student: Optional[str] = None
    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None

class PetitionStudentUpdate(PetitionStudentBase):
    pass
#all the updates should also hve to have validations and all fiels should be optional