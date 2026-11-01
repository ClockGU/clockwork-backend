from datetime import date
from json import JSONEncoder
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks

from api.env import settings
from api.handlers import EmailHandler, PetitionHandler
from api.handlers.dependencies import get_petition_handler
from api.pydantic_models import PetitionCreate, PetitionRead, PetitionSupervisorUpdate
from api.pydantic_models.dependencies import get_supervisor_petition_update_model
from api.security import generate_signature, get_current_supervisor


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


@router.post("/supervisor/petitions", response_model=PetitionRead)
async def create_petition(
    petition: PetitionCreate,
    background_tasks: BackgroundTasks,
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_supervisor),
):
    petition.user_account = user.get("sub")
    petition.supervisor_mail = user.get("email")
    created_petition = handler.create_petition(petition)

    email_handler = EmailHandler()
    signature = generate_signature()

    # Send email to all budget approvers with specific budget position ID
    for budget_position in created_petition.budget_positions:
        # Include budget position ID as third query parameter
        petition_url = f"{settings.FRONTEND_URL}/approver?petition_id={created_petition.id}&signature={signature}&budget_position_id={budget_position.id}"
        print(f"Budget Position URL: {petition_url}", flush=True)

        background_tasks.add_task(email_handler.send_budget_pos_mail, budget_position, petition_url)

    return created_petition


@router.get("/supervisor/petitions", response_model=List[PetitionRead])
def read_petitions_by_user(
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_supervisor),
):
    """
    LIST endpoint for a supervisor to get all petitions they are involved in.
    """
    petitions = handler.get_petitions_by_user(user.get("sub"))
    return petitions


@router.get("/supervisor/petitions/{petition_id}", response_model=PetitionRead)
def read_petition(
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_supervisor),
):
    petition = handler.get_petition()
    return petition


@router.patch("/supervisor/petitions/{petition_id}", response_model=PetitionRead)
def update_petition(
    petition_data: PetitionSupervisorUpdate = Depends(
        get_supervisor_petition_update_model
    ),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_supervisor),
):
    updated_petition = handler.update_petition_as_supervisor(petition_data)
    return updated_petition


@router.delete("/supervisor/petitions/{petition_id}")
def delete_petition(
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_supervisor),
):
    # TODO: Maybe simply calling handler.delete_petition() is not enough, we might need to add some mail logic to it.
    return handler.delete_petition()
