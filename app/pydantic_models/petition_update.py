from sqlmodel import SQLModel
from typing import Optional, Literal
from datetime import date
import uuid
from pydantic import field_validator, model_validator
import re


class PetitionBaseUpdate(SQLModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    minutes: Optional[int] = None
    student_mail: Optional[str] = None

    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None

    duration_exce_name: Optional[str] = None
    duration_exce_start: Optional[date] = None
    duration_exce_end: Optional[date] = None

    @field_validator("end_date")
    def validate_dates(cls, end_date, info):
        start_date = info.data.get("start_date")
        if start_date and end_date and end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        return end_date

    @field_validator("minutes")
    def validate_minutes(cls, minutes):
        if minutes is not None and minutes <= 0:
            raise ValueError("minutes must be greater than 0")
        return minutes

    @field_validator("student_mail")
    def validate_student_mail(cls, student_mail):
        # Ensure student_mail is a valid email format
        if student_mail and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", student_mail):
            raise ValueError("student_mail must be a valid email address")
        return student_mail

    @model_validator(mode="after")
    def validate_time_exc(cls, values):
        # Ensure all time_exc fields are either fully provided or all are None
        time_exc_fields = [
            values.time_exce_start,
            values.time_exce_end,
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


class PetitionSupervisorUpdate(PetitionBaseUpdate):
    user_account: Optional[uuid.UUID] = None
    org_unit: Optional[str] = None
    eos_number: Optional[str] = None
    ba_degree: Optional[bool] = None
    budget_position: Optional[str] = None
    budget_approver: Optional[str] = None

    status: Optional[Literal["pending", "approved", "rejected"]] = None

    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    duration_exce_course: Optional[bool] = None


class PetitionStudentUpdate(PetitionBaseUpdate):
    time_exce_student: Optional[str] = None
    duration_exce_student: Optional[str] = None

class PetitionClerkUpdate(PetitionBaseUpdate):
    user_account: Optional[uuid.UUID] = None
    org_unit: Optional[str] = None
    eos_number: Optional[str] = None
    ba_degree: Optional[bool] = None
    budget_position: Optional[str] = None
    budget_approver: Optional[str] = None

    status: Optional[Literal["pending", "approved", "student_action"]] = None

    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    duration_exce_course: Optional[bool] = None

class PetitionApproverUpdate(PetitionBaseUpdate):
    budget_approved: bool  # Make this field required
    status: Optional[Literal["pending", "approved","rejected", "student_action"]] = None