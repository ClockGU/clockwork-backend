"""
Implementation of Pydantic models for updating petitions.
The choice to overwrite the model_validate method is made to ensure that when updating
a petition, the new data is validated against the same rules as when creating a petition.
This ensures that the petition remains valid after updates.

Subclasses of PetitionUpdateBase can be created for different user roles (e.g., supervisor, clerk, student)
and implement role-specific validation logic if needed.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel
from sqlmodel import SQLModel
from sqlmodel.main import _TSQLModel

from api.consts import PetitionStatus

from ..db.schema import Petition
from . import PetitionCreate, PetitionRead
from .budget_position import BudgetPositionCreate
from .validators.petition_validators import (
    ClerkUpdateValidator,
    StudentUpdateValidator,
    SupervisorUpdateValidator,
)


class PetitionUpdateBase(SQLModel):
    org_unit: Optional[str] = None
    eos_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    minutes: Optional[int] = None
    ba_degree: Optional[bool] = None
    student_username: Optional[str] = None
    supervisor_mail: Optional[str] = None

    # Budget positions as a list - can be updated
    budget_positions: Optional[List[BudgetPositionCreate]] = None

    status: Optional[PetitionStatus] = None

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

    @classmethod
    def model_validate(
        cls: Type[_TSQLModel],
        obj: Any,
        existing: Petition,
        *,
        strict: Union[bool, None] = None,
        from_attributes: Union[bool, None] = None,
        context: Union[Dict[str, Any], None] = None,
        update: Union[Dict[str, Any], None] = None,
    ) -> _TSQLModel:
        """
        Implementation of pydantic model validation for updating a petition.

        On update a petition has to be still valid as if it was created.
        Therefore, we merge the existing petition data with the new data
        and validate it against the PetitionCreate model.

        We stricten the type of obj to the respective model class since the
        fastapi routes will use it as parser on the route anyway.

        Addition of existing to context.
        In order to utilize mixin validator classes that require access to the existing petition
        it is added to the context dict.
        """
        existing_read = PetitionRead.model_validate(existing)
        merged = existing_read.model_dump() | obj
        PetitionCreate.model_validate(merged)
        context = {**(context or {}), "existing": existing}
        return super(PetitionUpdateBase, cls).model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            update=update,
        )


class PetitionUpdate(PetitionUpdateBase):
    pass


class PetitionSupervisorUpdate(PetitionUpdate, SupervisorUpdateValidator):
    """
    Pydantic model for updating a petition by supervisor.
    Inherits from PetitionUpdateBase.
    Adds validation restricting updates for Supervisor role to petitions in status SUPERVISOR_ACTION.
    """

    pass


class PetitionClerkUpdate(PetitionUpdate, ClerkUpdateValidator):
    """
    Pydantic model for updating a petition by clerk.
    May have different permissions than supervisor updates.
    """

    approved: bool


class PetitionStudentUpdate(PetitionUpdate, StudentUpdateValidator):
    """
    Pydantic model for student petition acceptance.
    Only allows status updates with specific values.
    """

    approved: bool


class ClerkRevisionRequest(BaseModel):
    message: str
    subject: Optional[str] = None


class ClerkDeletionRequest(BaseModel):
    reason: str = ""


class StudenRevisionRequest(BaseModel):
    body: str
    subject: Optional[str] = None


PetitionUpdateModel = Union[
    PetitionSupervisorUpdate, PetitionClerkUpdate, PetitionStudentUpdate
]
