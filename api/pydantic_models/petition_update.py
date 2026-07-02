"""
Implementation of Pydantic models for updating petitions.
The choice to overwrite the model_validate method is made to ensure that when updating
a petition, the new data is validated against the same rules as when creating a petition.
This ensures that the petition remains valid after updates.

Subclasses of PetitionUpdateBase can be created for different user roles (e.g., supervisor, clerk, student)
and implement role-specific validation logic if needed.
"""

from sqlmodel import SQLModel
from typing import Optional, List, Type, Any, Union, Dict
from datetime import date
from pydantic import (
    BaseModel
    )

from sqlmodel.main import _TSQLModel
from api.consts import PetitionStatus
from . import PetitionCreate
from .budget_position import BudgetPositionCreate
from ..db.schema import Petition


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
        obj: _TSQLModel,
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
        """
        merged = existing.model_dump() | obj.model_dump(exclude_unset=True)
        PetitionCreate.model_validate(merged)
        return super(PetitionUpdateBase, cls).model_validate(obj, strict=strict,from_attributes=from_attributes, context=context, update=update)


class PetitionSupervisorUpdate(PetitionUpdateBase):
    """
    Pydantic model for updating a petition by supervisor.
    Inherits from PetitionUpdateBase.
    """
    pass


class PetitionClerkUpdate(BaseModel):
    """
    Pydantic model for updating a petition by clerk.
    May have different permissions than supervisor updates.
    """
    approved : bool

class PetitionStudentUpdate(BaseModel):
    """
    Pydantic model for student petition acceptance.
    Only allows status updates with specific values.
    """
    approved: bool

class PetitionApproverUpdate(PetitionUpdateBase):
    """
    Pydantic model for updating a petition by student.
    May have different permissions than supervisor and clerk updates.
    """
    pass

class ClerkRevisionRequest(BaseModel):
    message: str
    subject: Optional[str] = None

class ClerkDeletionRequest(BaseModel):
    reason: str = ""

class PetitionStudentUpdateRequest(BaseModel):
    body: str
    subject: Optional[str] = None
