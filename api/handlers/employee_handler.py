from io import BytesIO
from typing import List, Optional, Self
from uuid import UUID

from sqlmodel import Session

from api.db.managers.emploeyee_manager import EmployeeManager
from api.db.managers.petition_manager import PetitionManager
from api.db.schema.employee import Employee
from api.handlers.exception_handler import ExceptionHandler
from api.pdf.student_data import create_student_data_pdf
from api.pydantic_models import EmployeeRead, PetitionRead
from api.pydantic_models.employee import EmployeeCreate


class EmployeeHandler:
    def __init__(self, db: Session, object_instance: Optional[Employee] = None):
        self.manager = EmployeeManager(db)
        self.petition_manager = PetitionManager(db)
        self.exc = ExceptionHandler()
        self._object_instance = object_instance

    def get_object(self) -> Employee:
        if not self._object_instance:
            raise RuntimeError(
                "Calling get_object() is not allowed when no existing objects was provided at initialization."
            )
        return self._object_instance

    @classmethod
    def from_existing_object(cls, db: Session, object_instance: Employee) -> Self:
        """
        Explicitly create a EmployeeHandler instance from an existing Employee object.
        """
        return cls(db, object_instance)

    def create_employee(self, employee_data: EmployeeCreate) -> Employee:
        """
        Create a new employee record.
        """
        try:
            employee = self.manager.create_employee(employee_data)
        except Exception as e:
            raise self.exc.internal_error("creating the employee", e)
        if not employee:
            raise self.exc.created_failed("Employee")
        return employee

    def get_employee_by_user_account(self, user_account: UUID) -> Employee:
        """
        Retrieve an employee by their user_account UUID.
        """
        employee = self.manager.get_employee_by_user_account(user_account)
        if not employee:
            raise self.exc.not_found(
                "Employee",
                message=f"Employee with user_account {user_account} not found",
            )
        return employee

    def employee_exists_by_user_account(self, user_account: UUID) -> bool:
        """
        Check if an employee exists by their user_account UUID.
        """
        employee = self.manager.get_employee_by_user_account(user_account)
        return employee is not None

    def update_employee(self, employee: Employee, employee_data: dict) -> Employee:
        """
        Update an existing employee record.
        """

        # Proceed with the update
        updated_employee = self.manager.update_employee(employee, employee_data)
        if not updated_employee:
            raise self.exc.update_failed("Employee", str(employee))
        return updated_employee

    def delete_employee(self, employee_id: UUID) -> dict:
        """
        Delete an employee by their UUID.
        """
        # Check if the employee exists
        existing_employee = self.manager.get_employee(employee_id)
        if not existing_employee:
            raise self.exc.not_found("Employee", str(employee_id))

        # Proceed with the deletion
        success = self.manager.delete_employee(employee_id)
        if not success:
            raise self.exc.delete_failed("Employee", str(employee_id))
        return {"detail": "Employee deleted successfully"}

    def delete_employee_by_user_account(self, user_account: UUID) -> dict:
        """
        Delete an employee by their user_account UUID.
        """
        # Retrieve the employee by user_account
        employee = self.manager.get_employee_by_user_account(user_account)
        if not employee:
            raise self.exc.not_found(
                "Employee",
                message=f"Employee with user_account {user_account} not found",
            )

        # Ensure related documents are deleted (handled by cascade)
        success = self.manager.delete_employee(employee.id)
        if not success:
            raise self.exc.delete_failed(
                "Employee",
                message=f"Employee with user_account {user_account} could not be deleted",
            )
        return {"detail": "Employee and related documents deleted successfully"}

    def get_employee_by_username(self, username: str) -> Employee:
        """
        Retrieve an employee by their email and return their associated documents.
        """
        # Use the EmployeeManager to get the employee by email
        employee = self.manager.get_employee_by_username(username)
        if not employee:
            raise self.exc.not_found(
                "Employee", message=f"Employee with username {username} not found"
            )
        return employee

    def get_student_data_pdf(self, petition_id: UUID) -> BytesIO:
        """
        Generate and return student data PDF for a given petition ID.
        """
        # Get petition
        petition = self.petition_manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))

        student_username = petition.student_username
        if not student_username:
            raise self.exc.not_found("Petition", str(petition_id))

        # Get employee by username
        employee = self.manager.get_employee_by_username(student_username)
        if not employee:
            raise self.exc.not_found(
                "Employee",
                message=f"Employee with username {student_username} not found",
            )

        # Convert to Pydantic models
        employee_read = EmployeeRead.model_validate(employee, from_attributes=True)
        petition_read = PetitionRead.model_validate(petition)

        # Generate PDF
        try:
            pdf_buffer = create_student_data_pdf(employee_read, petition_read)
            return pdf_buffer
        except Exception as e:
            raise self.exc.internal_error("generating student data PDF", e)

    def get_employee_by_petition(self, petition_id: UUID) -> Employee:
        """
        Retrieve an employee by the petition ID they are associated with.
        """
        # Get the petition
        petition = self.petition_manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))

        # Get the student username from the petition
        student_username = petition.student_username
        if not student_username:
            raise self.exc.not_found(
                "Petition",
                str(petition_id),
                message=f"Petition with ID {petition_id} has no associated student username",
            )

        # Get the employee by username
        employee = self.manager.get_employee_by_username(student_username)
        if not employee:
            raise self.exc.not_found(
                "Employee",
                message=f"Employee with username {student_username} not found",
            )

        return employee
