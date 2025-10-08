from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from api.handlers.email_handler import EmailHandler

router = APIRouter()

class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str

@router.post("/send-email")
async def send_email(request: EmailRequest):
    """
    API endpoint to send an email.
    """
    email_handler = EmailHandler()  
    try:
        email_handler.send_email(
            recipient=request.recipient,
            subject=request.subject,
            body=request.body
        )
        return {"message": f"Email successfully sent to {request.recipient}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")