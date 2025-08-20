from sqlmodel import SQLModel
from typing import Optional, Literal, List
from datetime import date
import uuid
from pydantic import field_validator, model_validator
import re
from .budget_position import BudgetPositionCreate


class PetitionUpdateBase(SQLModel):
    org_unit: Optional[str] = None
    eos_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    minutes: Optional[int] = None
    ba_degree: Optional[bool] = None
    student_mail: Optional[str] = None
    supervisor_mail: Optional[str] = None

    # Budget positions as a list - can be updated
    budget_positions: Optional[List[BudgetPositionCreate]] = None

    status: Optional[Literal["pending", "approved", "student_action", "rejected"]] = None

    time_exce_student: Optional[bool] = None
    time_exce_course: Optional[bool] = None
    time_exce_name: Optional[str] = None
    time_exce_start: Optional[date] = None
    time_exce_end: Optional[date] = None

    duration_exce_course: Optional[bool] = None
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

    @field_validator("eos_number")
    def validate_eos_number(cls, eos_number):
        if eos_number is not None:
            # Ensure eos_number is numeric and has 5 digits
            if not re.match(r"^\d{5}$", eos_number):
                raise ValueError("eos_number must be a 5-digit numeric value")
        return eos_number

    @field_validator("student_mail")
    def validate_student_mail(cls, student_mail):
        if student_mail is not None:
            # Ensure student_mail is a valid email format
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", student_mail):
                raise ValueError("student_mail must be a valid email address")
        return student_mail

    @field_validator("budget_positions")
    def validate_budget_positions(cls, budget_positions):
        if budget_positions is not None and len(budget_positions) == 0:
            raise ValueError("At least one budget position is required if budget_positions is provided")
        return budget_positions

    @model_validator(mode="after")
    def validate_time_exc(cls, values):
        # Check if any time_exc fields are provided
        time_exc_fields = [
            values.time_exce_start,
            values.time_exce_end,
            values.time_exce_name,
        ]
        provided = [field for field in time_exc_fields if field is not None]
        
        # If some but not all are provided, raise error
        if 0 < len(provided) < len(time_exc_fields):
            raise ValueError("All time_exc fields must be provided together or not at all")
        return values

    @model_validator(mode="after")
    def validate_duration_exc(cls, values):
        # Check if any duration_exc fields are provided
        duration_exc_fields = [
            values.duration_exce_start,
            values.duration_exce_end,
            values.duration_exce_name,
        ]
        provided = [field for field in duration_exc_fields if field is not None]
        
        # If some but not all are provided, raise error
        if 0 < len(provided) < len(duration_exc_fields):
            raise ValueError("All duration_exc fields must be provided together or not at all")
        return values

    @model_validator(mode="after")
    def validate_budget_percentage_sum(cls, values):
        """Validate that budget position percentages sum up to 100 if budget_positions are provided"""
        budget_positions = values.budget_positions
        
        # Only validate if budget_positions are being updated
        if budget_positions is not None:
            if len(budget_positions) == 0:
                raise ValueError("At least one budget position is required if budget_positions is provided")
            
            # Calculate total percentage
            total_percentage = sum(budget_pos.percentage for budget_pos in budget_positions)
            
            # Check if total percentage equals 100
            if abs(total_percentage - 100.0) > 0.01:
                raise ValueError(f"Total budget position percentages must sum to 100, but got {total_percentage}")
        
        return values


class PetitionSupervisorUpdate(PetitionUpdateBase):
    """
    Pydantic model for updating a petition by supervisor.
    Inherits from PetitionUpdateBase.
    """
    pass


class PetitionClerkUpdate(PetitionUpdateBase):
    """
    Pydantic model for updating a petition by clerk.
    May have different permissions than supervisor updates.
    """
    pass

class PetitionStudentUpdate(SQLModel):
    """
    Pydantic model for student petition acceptance.
    Only allows status updates with specific values.
    """
    status: Literal["rejected", "clerk_action"]

class PetitionApproverUpdate(PetitionUpdateBase):
    """
    Pydantic model for updating a petition by student.
    May have different permissions than supervisor and clerk updates.
    """
    pass