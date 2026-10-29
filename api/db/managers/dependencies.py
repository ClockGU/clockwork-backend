from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlmodel import Session
from starlette.requests import Request

from api.db.dependencies import get_db
from api.db.managers import PetitionManager
from api.db.managers.emploeyee_manager import EmployeeManager
from api.db.managers.prev_employment_manager import PrevEmploymentManager
from api.db.managers.student_document import StudentDocumentManager
from api.db.schema import Employee, Petition, PrevEmployment
from api.db.schema.student_documents import StudentDocuments
from api.security import UserRole, decode_user_jwt, get_current_student


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

def get_specified_employee(
    employee_id: Optional[UUID] = None, db: Session = Depends(get_db)
) -> Optional[Employee]:
    """
    Dependency function to retrieve a specified employee if a employee_id was provided in the path.
    :raises: HTTPException with status code 404 if the employee is not found.
    """
    if not employee_id:
        return None

    existing_employee = EmployeeManager(db).get_employee(employee_id)
    if not existing_employee:
        raise HTTPException(
            status_code=404, detail=f"Employee with ID{str(employee_id)} not found"
        )
    return existing_employee

def get_specified_prev_employment(
    prev_employment_id: Optional[UUID] = None, db: Session = Depends(get_db)
) -> Optional[PrevEmployment]:
    """
    Dependency function to retrieve a specified employee if a employee_id was provided in the path.
    :raises: HTTPException with status code 404 if the employee is not found.
    """
    if not prev_employment_id:
        return None

    existing_prev_employment = PrevEmploymentManager(db).get_prev_employment(prev_employment_id)
    if not existing_prev_employment:
        raise HTTPException(
            status_code=404, detail=f"Employee with ID{str(prev_employment_id)} not found"
        )
    return existing_prev_employment


def get_document_for_clerk_or_owner(
    document_id: UUID,
    user: dict = Depends(decode_user_jwt),
    db: Session = Depends(get_db),
) -> StudentDocuments:
    """
    Dependency function to retrieve the specified document if the user is a clerk or the student owning it.
    :raises: HTTPException with status code 404 if the document is not found or not owned by the user,
    so the document's existence is not disclosed.
    """
    document = StudentDocumentManager(db).get_document(document_id)
    if not document or (
        user.get("user_role") != UserRole.CLERK.value
        and str(document.user_account) != user.get("sub")
    ):
        raise HTTPException(
            status_code=404, detail=f"Document with ID{str(document_id)} not found"
        )
    return document
