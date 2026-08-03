from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlmodel import Session
from starlette.requests import Request

from api.db.dependencies import get_db
from api.db.managers import PetitionManager
from api.db.managers.emploeyee_manager import EmployeeManager
from api.db.schema import Employee, Petition
from api.security import get_current_student


def get_specified_petition(
    petition_id: Optional[UUID] = None, db: Session = Depends(get_db)
) -> Optional[Petition]:
    """
    Dependency function to retrieve a specified petition if a petition_id was provided in the path.
    :raises: HTTPException with status code 404 if the petition is not found.
    """
    if not petition_id:
        return None

    existing_petition = PetitionManager(db).get_petition(petition_id)
    if not existing_petition:
        raise HTTPException(
            status_code=404, detail=f"Petition with ID{str(petition_id)} not found"
        )
    return existing_petition


def get_employee_for_student(
    student: dict = Depends(get_current_student), db: Session = Depends(get_db)
) -> Optional[Employee]:
    """
    Dependency function to retrieve a specified employee if a employee_id was provided in the path.
    :raises: HTTPException with status code 404 if the employee is not found.
    """
    if not student:
        return None

    existing_employee = EmployeeManager(db).get_employee_by_user_account(
        student.get("sub")
    )
    if not existing_employee:
        raise HTTPException(
            status_code=404,
            detail=f"Petition with ID{str(student.get("sub"))} not found",
        )
    return existing_employee
