import base64
import hashlib
import hmac
import json
import secrets
from collections.abc import Callable
from enum import Enum
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request

from api.db.schema import Petition
from api.env import settings

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
    try:
        scheme, token = auth_header.split()
    except ValueError:
        raise HTTPException(status_code=400, detail="Malformed Authorization header")
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


def get_current_clerk_or_student(user: dict = Depends(decode_user_jwt)):
    if user.get("user_role") not in [UserRole.CLERK.value, UserRole.STUDENT.value]:
        raise HTTPException(
            status_code=403, detail="No permission to access this resource"
        )
    return user


def auth_clerk_from_token(token: str):
    authenticate_role(user=decode_user_jwt(token=token), role=UserRole.CLERK.value)


def can_access(user: dict, obj) -> bool:
    role = user.get("user_role")
    if role == UserRole.CLERK.value:
        return True
    if isinstance(obj, Petition):
        if role == UserRole.SUPERVISOR.value:
            return str(obj.user_account) == user["sub"]
        if role == UserRole.STUDENT.value:
            return obj.student_username == user["username"]
        return False
    return (
        str(obj.user_account) == user["sub"]
    )  # Employee, StudentDocuments, PrevEmployment


SECRET_KEY = settings.SIGNATURE_SECRET_KEY  # Ensure the secret key is bytes


def generate_signature(budget_position_id: UUID) -> str:
    """
    Generate a unique HMAC signature using a random nonce and a secret key for a given BudgetPosition id.
    """
    nonce = secrets.token_urlsafe(32)  # Generates a secure random string
    msg = {"nonce": nonce, "budget_position_id": str(budget_position_id)}
    signature = hmac.new(
        SECRET_KEY, json.dumps(msg).encode("utf-8"), hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(nonce.encode() + b"." + signature).decode()
    return signature_b64


def verify_signature(signature_b64: str, budget_position_id: UUID) -> bool:
    """
    Verify if the given signature is valid for the provided budget_position_id using the secret key.
    """
    try:
        # Decode and split nonce and signature
        decoded = base64.urlsafe_b64decode(signature_b64.encode())
        nonce, received_sig = decoded.split(b".", 1)
        msg = {"nonce": nonce.decode(), "budget_position_id": str(budget_position_id)}
        # Recalculate the expected signature
        expected_sig = hmac.new(
            SECRET_KEY, json.dumps(msg).encode("utf-8"), hashlib.sha256
        ).digest()

        # Securely compare both signatures
        return hmac.compare_digest(received_sig, expected_sig)
    except Exception:
        return False
