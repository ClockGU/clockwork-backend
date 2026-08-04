from typing import Optional

from fastapi import Depends, BackgroundTasks
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import (
    get_employee_for_student,
    get_specified_petition,
)
from api.db.schema import Employee, Petition
from api.handlers import EmployeeHandler, PetitionHandler


def get_petition_handler(
    background_tasks: BackgroundTasks,
    petition: Optional[Petition] = Depends(get_specified_petition),
    db: Session = Depends(get_db)
) -> PetitionHandler:
    """
    Dependency function to provide a PetitionHandler depending on whether a petition was
    specified in the request.
    """
    if petition:
        return PetitionHandler.from_existing_object(db, petition, background_tasks)
    return PetitionHandler(db, background_tasks=background_tasks)


def get_employee_handler(
    employee: Optional[Employee] = Depends(get_employee_for_student),
    db: Session = Depends(get_db),
) -> EmployeeHandler:
    """
    Dependency function to provide a EmployeeHandler depending on whether a emplyoee was
    specified in the request.
    """
    if employee:
        return EmployeeHandler.from_existing_object(db, employee)
    return EmployeeHandler(db)
