import re
from typing import ClassVar, Self

from pydantic import field_validator, model_validator, ValidationError

from api.consts import LEGAL_REGULAR_CONTRACT_LENGTH, LEGAL_REGULAR_WORKTIME, PetitionStatus


class PetitionValidationMixin:
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
        if not re.match(r"^(F\d{6})$", eos_number):
            raise ValueError(
                "eos_number must be of the format FXXXXXX (Example: F12345)."
            )
        return eos_number

    @field_validator("budget_positions")
    def validate_budget_positions(cls, budget_positions):
        if not budget_positions or len(budget_positions) == 0:
            raise ValueError("At least one budget position is required")
        return budget_positions

    @model_validator(mode="after")
    def validate_time_exc(cls, values):
        # Ensure all time_exc fields are either fully provided or all are None
        time_exc_fields = [
            values.time_exce_name,
            values.time_exce_start,
            values.time_exce_end,
            values.time_exce_time,
        ]
        provided = [field for field in time_exc_fields if field is not None]
        if (values.time_exce_student is None or values.time_exce_student is False) and len(provided) > 0 and len(provided) != len(time_exc_fields):
            raise ValueError(
                "All time_exc fields must be provided together or not at all"
            )
        return values

    @model_validator(mode="after")
    def validate_duration_exc(cls, values):
        # Ensure all duration_exc fields are either fully provided or all are None
        duration_exc_fields = [
            values.duration_exce_name,
            values.duration_exce_start,
            values.duration_exce_end,
        ]
        provided = [field for field in duration_exc_fields if field is not None]
        if (values.duration_exce_course is None or values.duration_exce_course is False) and len(provided) > 0 and len(provided) != len(duration_exc_fields):
            raise ValueError(
                "All duration_exc fields must be provided together or not at all"
            )
        return values

    @model_validator(mode="after")
    def validate_duration_requirement(cls, values):
        if values.start_date and values.end_date:
            days_diff = (values.end_date - values.start_date).days
            if (
                days_diff < LEGAL_REGULAR_CONTRACT_LENGTH
            ):  # roughly 1 year (365 days) minus 1 for inclusive dates
                if not values.duration_exce_name:
                    raise ValueError(
                        "Contract duration is less than 1 year, duration_exception fields must be provided"
                    )
        return values

    @model_validator(mode="after")
    def validate_time_requirement(cls, values):
        if (
            values.minutes is not None and values.minutes < LEGAL_REGULAR_WORKTIME
        ):  # 40 hours * 60 minutes
            if not values.time_exce_name:
                raise ValueError(
                    "Worktime is less than 40h/month, time_exception fields must be provided"
                )
        return values

    @model_validator(mode="after")
    def validate_budget_percentage_sum(cls, values):
        """Validate that budget position percentages sum up to 100"""
        budget_positions = values.budget_positions

        # Calculate total percentage (individual validations are handled by BudgetPositionCreate)
        # TODO: Change Percentage from decimal representation to intiger representation (e.g., 25% as 25) to avoid floating point issues
        total_percentage = sum(budget_pos.percentage for budget_pos in budget_positions)

        # Check if total percentage equals 100 (with small tolerance for floating point precision)
        if abs(total_percentage - 100.0) > 0.01:
            raise ValueError(
                f"Total budget position percentages must sum to 100, but got {total_percentage}"
            )

        return values

class RoleUpdateValidator:
    """
    Base class for role-based update validators.
    Subclasses should define the allowed petition statuses
    in which the specific role is allowed to update petitions.
    """
    allowed_petition_statuses: ClassVar[list[PetitionStatus]]
    @model_validator(mode="after")
    def validate_status_in_supervisor_action(self, info) -> Self:
        existing = info.context.get("existing", None)
        if not existing: raise RuntimeError("UpdateModelValidator requires an existing model instance in context")
        if existing.status not in self.allowed_petition_statuses:
            raise ValueError(
                f"Petition status must be one of ({self.allowed_petition_statuses}) for this role to update a petition."
            )
        return self

class SupervisorUpdateValidator(RoleUpdateValidator):
    """
    Mixin class to validate that the petition status is in the correct status for a
    supervisor to update the petition.
    """
    allowed_petition_statuses = [PetitionStatus.STUDENT_REVISION, PetitionStatus.APPROVER_REVISION]

class StudentUpdateValidator(RoleUpdateValidator):
    """
    Mixin class to validate that the petition status is in the correct status for a
    student to update the petition.
    """
    allowed_petition_statuses = [PetitionStatus.CLERK_REVISION,PetitionStatus.STUDENT_ACTION]

class ClerkUpdateValidator(RoleUpdateValidator):
    """
    Mixin class to validate that the petition status is in the correct status for a
    student to update the petition.
    """
    allowed_petition_statuses = [PetitionStatus.CLERK_ACTION, PetitionStatus.AWAITING_SIGNATURE]