from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session
from json import dumps, JSONEncoder
from datetime import date

from api.handlers import PetitionHandler, EmailHandler
from api.pydantic_models import (
    PetitionSupervisorCreate,
    PetitionRead,
    PetitionSupervisorUpdate
)
from api.db.dependencies import get_db
from api.security import (
    get_current_supervisor, 
    get_current_student, 
    get_current_clerk,
    generate_signature,
    verify_signature
)
from api.routers.web_socket import send_data_to_socket

# Custom JSON encoder to handle UUIDs and dates
class UUIDEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)  # Convert UUID to string
        if isinstance(obj, date):
            return obj.isoformat()  # Convert date to ISO 8601 string
        return super().default(obj)

router = APIRouter()

## these are the api's fo petitions related to supervisor


def get_petition_handler(
        db: Session = Depends(get_db)
        ) -> PetitionHandler:
    return PetitionHandler(db)

@router.post("/supervisor/petitions/", response_model=PetitionRead)
async def create_petition(
    petition: PetitionSupervisorCreate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petition.user_account = user.get('sub')
    petition.supervisor_mail = user.get('email')
    created_petition = handler.create_petition(petition)

    email_handler = EmailHandler()
    signature = generate_signature()
    
    # Send email to all budget approvers with specific budget position ID
    for budget_position in created_petition.budget_positions:
        # Include budget position ID as third query parameter
        petition_url = f"https://preview.clock.uni-frankfurt.de/approver?petition_id={created_petition.id}&signature={signature}&budget_position_id={budget_position.id}"
        print(f"Budget Position URL: {petition_url}", flush=True)
        
        email_handler.send_email(
            recipient=budget_position.budget_approver,
            subject="New petition requires your approval",
            body=f"New petition is created for budget position: {budget_position.budget_position}. Here is the link to access that petition: {petition_url}"
        )
    
    # Get all the clerks and broadcast
    petitions = handler.list_petitions()
    clerk_IDS = ["1234", "12345"]  # Once the clerks have registered the data will be fetched from the database
    for clerk_id in clerk_IDS:
        await send_data_to_socket(
            user_id=clerk_id,
            data=dumps({
                "type": "new_petition",
                "data": [petition.dict(by_alias=True, exclude_none=True) for petition in petitions]  # Convert each model to a dictionary
            }, cls=UUIDEncoder)  # Use custom encoder
        )
    
    return created_petition

@router.get("/supervisor/petitions/user", response_model=List[PetitionRead])
def read_petitions_by_user(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_clerk)
):
    petitions = handler.get_petitions_by_user(user.get('sub'))
    return petitions

@router.get("/supervisor/petitions/", response_model=List[PetitionRead])
def read_petitions(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
): 
    petitions = handler.list_petitions()
    return petitions

@router.get("/supervisor/petitions/{petition_id}", response_model=PetitionRead)
def read_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    petition = handler.get_petition(petition_id)
    return petition

@router.patch("/supervisor/petitions/{petition_id}", response_model=PetitionRead)
def update_petition(
    petition_id: UUID,
    petition: PetitionSupervisorUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    updated_petition = handler.update_petition(petition_id, petition)
    return updated_petition

@router.delete("/supervisor/petitions/{petition_id}")
def delete_petition(
    petition_id: UUID,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_supervisor)
):
    success = handler.delete_petition(petition_id)
    return {"detail": "Petition deleted successfully"}


