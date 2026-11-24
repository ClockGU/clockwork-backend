import base64
import hashlib
import hmac
import secrets
from collections.abc import Callable
from enum import Enum

import jwt
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from api.db.dependencies import get_db
from api.env import settings
from api.handlers.document_handler import StudentDocumentHandler
from api.handlers.employee_handler import EmployeeHandler
from api.pydantic_models.employee import EmployeeCreate

# Replace with your actual public key
PUBLIC_KEY_PATH = settings.JWT_PUBLIC_KEY_PATH
JWT_ALGORITHM = settings.JWT_ALGORITHM

if not PUBLIC_KEY_PATH:
    raise Exception("JWT public certificate is not provided")
with open(PUBLIC_KEY_PATH, "r") as f:
    PUBLIC_KEY = f.read()


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
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[JWT_ALGORITHM])

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def authenticate_role(user: dict, role: int):
    if user.get("user_role") != role:
        raise HTTPException(
            status_code=403, detail="No permission to access this resource"
        )
    return user

def build_current_role_retrival(role: UserRole) -> Callable[[], dict]:
    """
    A factory function building an authentication function for a role provided.
    The authentication function can be used as a dependency for endpoints. It
    attempts to read a 'Bearer' toke from the requests headers, tries to decode
    a JWT from it and checks whether the decoded user object has the specified role.
    """
    def get_current_role(user: dict = Depends(decode_user_jwt)):
        return authenticate_role(user, role.value)
    func_name = f"get_current_{role.name.lower()}"
    get_current_role.__name__ = func_name
    get_current_role.__qualname__ = func_name
    return get_current_role


get_current_student = build_current_role_retrival(UserRole.STUDENT)
get_current_supervisor = build_current_role_retrival(UserRole.SUPERVISOR)
get_current_clerk = build_current_role_retrival(UserRole.CLERK)

def get_current_clerk_or_student(request: Request):
    token = retrieve_jwt_bearer_token(request)
    user = decode_user_jwt(token)
    if user.get("user_role") not in [UserRole.CLERK.value, UserRole.STUDENT.value]:
        raise HTTPException(
            status_code=403, detail="No permission to access this resource"
        )
    return user

def auth_clerk_from_token(token: str):
    authenticate_role(user=decode_user_jwt(token=token), role=UserRole.CLERK.value)

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
