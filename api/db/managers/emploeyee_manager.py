from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from api.db.schema.employee import Employee
from api.pydantic_models.employee import EmployeeCreate


class EmployeeManager:
    def __init__(self, db: Session):
        self.db = db
        self.schema = Employee  # Reference to the Employee model

    def create_employee(self, employee_data: EmployeeCreate) -> Employee:
        """
        Create a new employee record.
        """
        employee_dict = employee_data.model_dump()
        employee = self.schema.model_validate(employee_dict)
        try:
            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)
            return employee
        except IntegrityError:
            self.db.rollback()
            return self.get_employee_by_user_account(employee_data.user_account)

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

    def get_employee_by_username(self, username: str) -> Optional[Employee]:
        """
        Retrieve an employee by their email address.
        """
        statement = select(self.schema).where(self.schema.username == username)
        result = self.db.execute(statement)
        return result.scalars().first()

    def update_employee(
        self, employee: Employee, employee_data: dict
    ) -> Optional[Employee]:
        """
        Update an existing employee record.
        """
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
