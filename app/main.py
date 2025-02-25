from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.openapi.utils import get_openapi


from app.db.dependencies import get_db  
from app.security import get_current_supervisor
from app.routers import router

app = FastAPI()

app.include_router(router)



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




@app.get("/checkuser")
def check_user(
    current_user: dict = Depends(get_current_supervisor)
    ):
    return current_user

# routes to check the basic working
@app.get("/check-db")
def check_db(
    db: Session = Depends(get_db)
    ):
    result = db.execute(text("SELECT NOW()"))  # Query to get the current timestamp from the database
    current_time = result.scalar()  # Fetch the first row's first column (current timestamp)
    return {"database_time": current_time}




