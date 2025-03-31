from fastapi import Request, HTTPException, Depends
import jwt
from enum import Enum


from app.env import settings
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

def get_current_supervisor(request: Request):
    """
    decode the JWT token to inject user in api and checks the role of supervisor
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
        
        ####check the role of supervisor
        if payload.get("user_role") != UserRole.SUPERVISOR.value:
            raise HTTPException(status_code=403, detail="No permission to access this resource")
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    

def get_current_student(request: Request):
    """
    decode the JWT token to inject user in api and checks the role of student
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
        
        ####check the role of student here
        if payload.get("user_role") != UserRole.STUDENT.value:
            raise HTTPException(status_code=403, detail="No permission to access this resource")


        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
