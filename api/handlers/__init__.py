from .petition_handler import PetitionHandler
from .document_handler import StudentDocumentHandler
from .employee_handler import EmployeeHandler
from .email_handler import EmailHandler
from .socker_handler import ConnectionManager
from api.security import auth_clerk_from_token

ClerkConnectionManager = ConnectionManager(auth_clerk_from_token)
