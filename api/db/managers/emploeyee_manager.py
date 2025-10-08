from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select

from api.db.schema.employee import Employee


class EmployeeManager:
    def __init__(self, db: Session):
        self.db = db
        self.schema = Employee  # Reference to the Employee model

    def create_employee(self, employee_data: Employee) -> Employee:
        """
        Create a new employee record.
        """
        self.db.add(employee_data)
        self.db.commit()
        self.db.refresh(employee_data)
        return employee_data

    def get_employee(self, employee_id: UUID) -> Optional[Employee]:
        """
        Retrieve a single employee by their UUID.
        """
        return self.db.get(self.schema, employee_id)

    def get_employees(self, offset: int = 0, limit: int = 100) -> List[Employee]:
        """
        Retrieve a list of employees with pagination.
        """
        statement = select(self.schema).offset(offset).limit(limit)
        result = self.db.execute(statement)
        return result.scalars().all()

    def get_employee_by_user_account(self, user_account: UUID) -> Optional[Employee]:
        """
        Retrieve an employee by their user_account UUID.
        """
        statement = select(self.schema).where(self.schema.user_account == user_account)
        result = self.db.execute(statement)
        return result.scalars().first()

    def get_employee_by_email(self, email: str) -> Optional[Employee]:
        """
        Retrieve an employee by their email address.
        """
        statement = select(self.schema).where(self.schema.user_email == email)
        result = self.db.execute(statement)
        return result.scalars().first()

    def update_employee(self, employee_id: UUID, employee_data: dict) -> Optional[Employee]:
        """
        Update an existing employee record.
        """
        employee = self.db.get(self.schema, employee_id)
        if not employee:
            return None

        # Update only the provided fields
        for key, value in employee_data.items():
            setattr(employee, key, value)

        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def delete_employee(self, employee_id: UUID) -> bool:
        """
        Delete an employee by their UUID.
        """
        employee = self.db.get(self.schema, employee_id)
        if not employee:
            return False

        self.db.delete(employee)
        self.db.commit()
        return True