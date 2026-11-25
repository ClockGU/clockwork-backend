from typing import Optional

from fastapi import BackgroundTasks, Depends
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import (
    get_specified_employee,
    get_specified_petition,
    get_specified_prev_employment,
)
from api.db.schema import Employee, Petition, PrevEmployment
from api.handlers import EmployeeHandler, PetitionHandler
from api.handlers.prev_employment_handler import PrevEmploymentHandler


def get_petition_handler(
    background_tasks: BackgroundTasks,
    petition: Optional[Petition] = Depends(get_specified_petition),
    db: Session = Depends(get_db),
) -> PetitionHandler:
    """
    Dependency function to provide a PetitionHandler depending on whether a petition was
    specified in the request.
    """
    if petition:
        return PetitionHandler.from_existing_object(db, petition, background_tasks)
    return PetitionHandler(db, background_tasks=background_tasks)


def get_employee_handler(
    employee: Optional[Employee] = Depends(get_specified_employee),
    db: Session = Depends(get_db),
) -> EmployeeHandler:
    """
    Dependency function to provide a EmployeeHandler depending on whether a emplyoee was
    specified in the request.
    """
    if employee:
        return EmployeeHandler.from_existing_object(db, employee)
    return EmployeeHandler(db)


def get_prev_employment_handler(
    prev_employment: Optional[PrevEmployment] = Depends(get_specified_prev_employment),
    db: Session = Depends(get_db),
) -> PrevEmploymentHandler:
    if prev_employment:
        return PrevEmploymentHandler.from_existing_object(
            db, object_instance=prev_employment
        )
    return PrevEmploymentHandler(db)
