from fastapi import Request, HTTPException, Depends
import jwt

from app.env import settings
# Replace with your actual public key
PUBLIC_KEY_PATH = settings.JWT_PUBLIC_KEY_PATH
JWT_ALGORITHM = settings.JWT_ALGORITHM

if not PUBLIC_KEY_PATH:
    raise Exception("JWT public certificate is not provided")
with open(PUBLIC_KEY_PATH, "r") as f:
    public_key = f.read()


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

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
