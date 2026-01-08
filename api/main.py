from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from typing import Dict

from api.db.dependencies import get_db, engine
from api.security import get_current_supervisor, get_current_student
from api.routers import router
from api.admin import setup_admin
from api.env import settings

app = FastAPI()

# Add session middleware for admin authentication
app.add_middleware(
    SessionMiddleware, 
    secret_key=str(settings.SIGNATURE_SECRET_KEY.decode() if isinstance(settings.SIGNATURE_SECRET_KEY, bytes) else settings.SIGNATURE_SECRET_KEY)
)

# Setup admin panel
setup_admin(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,  # Allow origins from env
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(router)


### Custom OpenAPI schema generation for swagger docs
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    # Generate the default OpenAPI schema
    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="API documentation with CAS authentication",
        routes=app.routes,
    )

    # Get existing components or create an empty dict
    components = openapi_schema.get("components", {})

    # Add or update the security schemes
    components["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token in the 'Authorization' header as 'Bearer <your-token>'"
        }
    }

    # Assign the updated components back to the schema
    openapi_schema["components"] = components

    # Apply the security globally
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/checksupervisor")
def check_supervisor(
    current_user: dict = Depends(get_current_supervisor)
    ):
    return current_user

@app.get("/checkstudent")
def check_student(
    current_user: dict = Depends(get_current_student)
    ):
    return current_user

# routes to check the basic working
@app.get("/check-db")
def check_db(db: Session = Depends(get_db)):
    if db.bind.dialect.name == "sqlite":
        query = "SELECT CURRENT_TIMESTAMP"
    else:
        query = "SELECT NOW()"
    result = db.execute(text(query))
    current_time = result.scalar()
    return {"database_time": current_time}





