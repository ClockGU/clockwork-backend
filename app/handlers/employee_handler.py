from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from fastapi import HTTPException

from app.db.managers.emploeyee_manager import EmployeeManager
from app.db.schema.employee import Employee


class EmployeeHandler:
    def __init__(self, db: Session):
        self.manager = EmployeeManager(db)

    def create_employee(self, employee_data: dict) -> Employee:
        """
        Create a new employee record.
        """
        try:
            # Convert the dictionary to an Employee instance
            employee_instance = Employee(**employee_data)
            employee = self.manager.create_employee(employee_instance)
            if not employee:
                raise HTTPException(status_code=400, detail="Employee could not be created")
            return employee
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"An error occurred while creating the employee: {str(e)}"
            )

    def get_employee(self, employee_id: UUID) -> Employee:
        """
        Retrieve a single employee by their UUID.
        """
        employee = self.manager.get_employee(employee_id)
        if not employee:
            raise HTTPException(
                status_code=404, detail=f"Employee with ID {employee_id} not found"
            )
        return employee

    def get_employee_by_user_account(self, user_account: UUID) -> Employee:
        """
        Retrieve an employee by their user_account UUID.
        """
        employee = self.manager.get_employee_by_user_account(user_account)
        if not employee:
            raise HTTPException(
                status_code=404, detail=f"Employee with user_account {user_account} not found"
            )
        return employee

    def employee_exists_by_user_account(self, user_account: UUID) -> bool:
        """
        Check if an employee exists by their user_account UUID.
        """
        employee = self.manager.get_employee_by_user_account(user_account)
        return employee is not None

    def list_employees(self, offset: int = 0, limit: int = 100) -> List[Employee]:
        """
        Retrieve a list of employees with pagination.
        """
        employees = self.manager.get_employees(offset=offset, limit=limit)
        if not employees:
            raise HTTPException(status_code=404, detail="No employees found")
        return employees

    def update_employee(self, employee_id: UUID, employee_data: dict) -> Employee:
        """
        Update an existing employee record.
        """
        # Check if the employee exists
        existing_employee = self.manager.get_employee(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=404, detail=f"Employee with ID {employee_id} not found"
            )

        # Proceed with the update
        updated_employee = self.manager.update_employee(employee_id, employee_data)
        if not updated_employee:
            raise HTTPException(
                status_code=400, detail=f"Employee with ID {employee_id} could not be updated"
            )
        return updated_employee

    def delete_employee(self, employee_id: UUID) -> dict:
        """
        Delete an employee by their UUID.
        """
        # Check if the employee exists
        existing_employee = self.manager.get_employee(employee_id)
        if not existing_employee:
            raise HTTPException(
                status_code=404, detail=f"Employee with ID {employee_id} not found"
            )

        # Proceed with the deletion
        success = self.manager.delete_employee(employee_id)
        if not success:
            raise HTTPException(
                status_code=400, detail=f"Employee with ID {employee_id} could not be deleted"
            )
        return {"detail": "Employee deleted successfully"}

    def delete_employee_by_user_account(self, user_account: UUID) -> dict:
        """
        Delete an employee by their user_account UUID.
        """
        # Retrieve the employee by user_account
        employee = self.manager.get_employee_by_user_account(user_account)
        if not employee:
            raise HTTPException(
                status_code=404, detail=f"Employee with user_account {user_account} not found"
            )

        # Ensure related documents are deleted (handled by cascade)
        success = self.manager.delete_employee(employee.id)
        if not success:
            raise HTTPException(
                status_code=400, detail=f"Employee with user_account {user_account} could not be deleted"
            )
        return {"detail": "Employee and related documents deleted successfully"}
    

    # the issue of employee not found
    # find it and get done with it.
