from sqlmodel import SQLModel
from typing import Optional, Literal, List
from datetime import date
import uuid
from pydantic import field_validator, model_validator, BaseModel
import re
from .budget_position import BudgetPositionCreate


class PetitionCreateBase(SQLModel):
    user_account: Optional[uuid.UUID] = None
    org_unit: str
    eos_number: str
    start_date: date
    end_date: date
    minutes: int

    student_username: str
    supervisor_mail: Optional[str] = None

    # Budget positions as a list
    budget_positions: List[BudgetPositionCreate]


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
        # Ensure eos_number starts with 'F' followed by 6 digits
        if not re.match(r"^F\d{6}$", eos_number):
            raise ValueError("eos_number must start with 'F' followed by 6 digits (e.g., F123456)")
        return eos_number

    @field_validator("student_username")
    def validate_student_username(cls, student_username):

        if student_username is None or student_username == "":
            raise ValueError("student_username is required")
        return student_username

    @field_validator("budget_positions")
    def validate_budget_positions(cls, budget_positions):
        if not budget_positions or len(budget_positions) == 0:
            raise ValueError("At least one budget position is required")
        return budget_positions

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

    @model_validator(mode="after")
    def validate_budget_percentage_sum(cls, values):
        """Validate that budget position percentages sum up to 100"""
        budget_positions = values.budget_positions
        
        if not budget_positions:
            raise ValueError("At least one budget position is required")
        
        # Calculate total percentage (individual validations are handled by BudgetPositionCreate)
        total_percentage = sum(budget_pos.percentage for budget_pos in budget_positions)
        
        # Check if total percentage equals 100 (with small tolerance for floating point precision)
        if abs(total_percentage - 100.0) > 0.01:
            raise ValueError(f"Total budget position percentages must sum to 100, but got {total_percentage}")
        
        return values


class PetitionSupervisorCreate(PetitionCreateBase):
    """
    Pydantic model for creating a new petition.
    Inherits from PetitionCreateBase.
    """
    pass


class PetitionStudentAction(BaseModel):
    approved: bool

class PetitionCreate(PetitionCreateBase):
    """
    Pydantic model for creating a new petition.
    Inherits from PetitionCreateBase.
    """
    pass