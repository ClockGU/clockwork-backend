import jwt
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from api.db.schema.budget_position import BudgetPosition
from api.db.schema.employee import Employee
from api.db.schema.petition import Petition
from api.db.schema.student_documents import StudentDocuments
from api.env import settings


class AdminAuth(AuthenticationBackend):
    """Authentication backend for SQLAdmin using JWT tokens"""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # For now, use a simple hardcoded check
        # You can replace this with your actual authentication logic
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            # Store authentication in session
            request.session.update({"authenticated": True, "username": username})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Check if user is authenticated via admin session only.
        Admin authentication is completely separate from regular user JWT tokens.
        """
        # Only check session-based authentication
        return request.session.get("authenticated", False)


class PetitionAdmin(ModelView, model=Petition):
    name = "Petition"
    name_plural = "Petitions"
    icon = "fa-solid fa-file-invoice"

    column_list = [
        Petition.id,
        Petition.student_username,
        Petition.status,
        Petition.start_date,
        Petition.end_date,
        Petition.minutes,
        Petition.supervisor_mail,
        Petition.org_unit,
    ]

    column_searchable_list = [
        Petition.student_username,
        Petition.supervisor_mail,
        Petition.status,
    ]

    column_sortable_list = [
        Petition.start_date,
        Petition.end_date,
        Petition.status,
    ]

    column_default_sort = [(Petition.start_date, True)]

    form_excluded_columns = [Petition.budget_positions]


class EmployeeAdmin(ModelView, model=Employee):
    name = "Employee"
    name_plural = "Employees"
    icon = "fa-solid fa-user"

    column_list = [
        Employee.id,
        Employee.username,
        Employee.first_name,
        Employee.last_name,
        Employee.date_of_birth,
        Employee.address,
        Employee.postal_code,
        Employee.nationality,
    ]

    column_searchable_list = [
        Employee.username,
        Employee.first_name,
        Employee.last_name,
    ]

    column_sortable_list = [
        Employee.username,
        Employee.first_name,
        Employee.last_name,
    ]

    form_excluded_columns = [Employee.documents]


class BudgetPositionAdmin(ModelView, model=BudgetPosition):
    name = "Budget Position"
    name_plural = "Budget Positions"
    icon = "fa-solid fa-dollar-sign"

    column_list = [
        BudgetPosition.id,
        BudgetPosition.petition_id,
        BudgetPosition.budget_position,
        BudgetPosition.budget_approver,
        BudgetPosition.budget_position_approved,
        BudgetPosition.percentage,
    ]

    column_searchable_list = [
        BudgetPosition.budget_approver,
        BudgetPosition.budget_position,
    ]

    column_sortable_list = [
        BudgetPosition.budget_position_approved,
        BudgetPosition.percentage,
    ]


class StudentDocumentsAdmin(ModelView, model=StudentDocuments):
    name = "Student Document"
    name_plural = "Student Documents"
    icon = "fa-solid fa-folder-open"

    column_list = [
        StudentDocuments.id,
        StudentDocuments.employee_id,
        StudentDocuments.elstam_url,
        StudentDocuments.studienbescheinigung_url,
        StudentDocuments.versicherungsbescheinigung_url,
        StudentDocuments.sozialversicherungsbogen_url,
    ]

    column_searchable_list = [
        StudentDocuments.employee_id,
    ]


def setup_admin(app, engine):
    """Setup SQLAdmin with all model views and authentication"""
    secret_key = (
        settings.SIGNATURE_SECRET_KEY.decode()
        if isinstance(settings.SIGNATURE_SECRET_KEY, bytes)
        else settings.SIGNATURE_SECRET_KEY
    )
    authentication_backend = AdminAuth(secret_key=secret_key)
    admin = Admin(
        app,
        engine,
        title="ClockWork Admin",
        authentication_backend=authentication_backend,
    )

    # Register all admin views
    admin.add_view(PetitionAdmin)
    admin.add_view(EmployeeAdmin)
    admin.add_view(BudgetPositionAdmin)
    admin.add_view(StudentDocumentsAdmin)

    return admin
