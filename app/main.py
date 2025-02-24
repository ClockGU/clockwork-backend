from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.openapi.utils import get_openapi


from app.dependencies import get_db  
from app.security import get_current_supervisor

app = FastAPI()



def custom_openapi():
    """
    This function will be used to generate the OpenAPI schema with the custom security scheme.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="API documentation with CAS authentication",
        routes=app.routes,
    )
    
    openapi_schema["components"] = {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter JWT token in the 'Authorization' header as 'Bearer <your-token>'"
            }
        }
    }
    
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




