from fastapi import Request, HTTPException, Depends
import jwt
from enum import Enum
from sqlmodel import Session
import hmac
import hashlib
import base64
import secrets
from api.env import settings
from api.handlers import ConnectionManager
from api.handlers.employee_handler import EmployeeHandler
from api.handlers.document_handler import StudentDocumentHandler
from api.db.dependencies import get_db

# Replace with your actual public key
PUBLIC_KEY_PATH = settings.JWT_PUBLIC_KEY_PATH
JWT_ALGORITHM = settings.JWT_ALGORITHM

if not PUBLIC_KEY_PATH:
    raise Exception("JWT public certificate is not provided")
with open(PUBLIC_KEY_PATH, "r") as f:
    public_key = f.read()


class UserRole(Enum):
    STUDENT = 0
    SUPERVISOR = 1
    CLERK = 2


def retrieve_jwt_bearer_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, token = auth_header.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    return token


def decode_user_jwt(token: str = Depends(retrieve_jwt_bearer_token)):
    try:
        # Decode the JWT token using the public key
        payload = jwt.decode(token, public_key, algorithms=[JWT_ALGORITHM])

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def authenticate_clerk(user: dict):
    if user.get("user_role") != UserRole.CLERK.value:
        raise HTTPException(status_code=403, detail="No permission to access this resource")
    return user


def get_current_supervisor(request: Request):
    """
    decode the JWT token to inject user in api and checks the role of supervisor
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, token = auth_header.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    try:
        # Decode the JWT token using the public key
        payload = jwt.decode(token, public_key, algorithms=[JWT_ALGORITHM])
        ####check the role of supervisor
        if payload.get("user_role") != UserRole.SUPERVISOR.value:
            raise HTTPException(status_code=403, detail="No permission to access this resource")
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def get_current_student(request: Request, db: Session = Depends(get_db)):
    """
    Decode the JWT token to inject user in API and checks the role of student.
    If no employee entry exists for the user, create one and also create a document entry.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        # Decode the JWT token using the public key
        payload = jwt.decode(token, public_key, algorithms=[JWT_ALGORITHM])

        # Check the role of student
        if payload.get("user_role") != UserRole.STUDENT.value:
            raise HTTPException(status_code=403, detail="No permission to access this resource")

        # Extract user_account from the payload
        user_account = payload.get("sub")
        if not user_account:
            raise HTTPException(status_code=400, detail="Invalid token: Missing user_account")

        # Dependency injection for handlers
        employee_handler = EmployeeHandler(db)
        document_handler = StudentDocumentHandler(db)

        # Check if an employee entry exists

        if not employee_handler.employee_exists_by_user_account(user_account):
            # Create a new employee entry
            new_employee_data = {
                "user_account": user_account,
                "username": payload.get("username"),
            }
            new_employee = employee_handler.create_employee(new_employee_data)

            # Create a new document entry for the employee
            document_handler.manager.create_document({"employee_id": new_employee.id})
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def get_current_clerk(user: dict = Depends(decode_user_jwt)) -> dict:
    """
    decode the JWT token to inject user in api and checks the role of clerk
    """
    authenticate_clerk(user)
    return user


def get_clerk_connection_manager() -> ConnectionManager:
    def authenticate(token: str) -> None:
        authenticate_clerk(user=decode_user_jwt(token=token))
    return ConnectionManager(authenticate)


# for email signature
SECRET_KEY = settings.SIGNATURE_SECRET_KEY  # Ensure the secret key is bytes


def generate_signature() -> str:
    """
    Generate a unique HMAC signature using a random nonce and a secret key.
    """
    nonce = secrets.token_urlsafe(32)  # Generates a secure random string
    signature = hmac.new(SECRET_KEY, nonce.encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(nonce.encode() + b"." + signature).decode()
    return signature_b64


def verify_signature(signature_b64: str) -> bool:
    """
    Verify if the given signature is valid using the secret key.
    """
    try:
        # Decode and split nonce and signature
        decoded = base64.urlsafe_b64decode(signature_b64.encode())
        nonce, received_sig = decoded.split(b".", 1)

        # Recalculate the expected signature
        expected_sig = hmac.new(SECRET_KEY, nonce, hashlib.sha256).digest()

        # Securely compare both signatures
        return hmac.compare_digest(received_sig, expected_sig)
    except Exception:
        return False
