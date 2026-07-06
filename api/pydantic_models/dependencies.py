from uuid import UUID

from fastapi import Depends, HTTPException
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers import PetitionManager
from api.pydantic_models import PetitionSupervisorUpdate, PetitionClerkUpdate


def get_supervisor_petition_update_model(petition_id:UUID, body:dict, db: Session = Depends(get_db)) -> PetitionSupervisorUpdate:
    """
    Returns a PetitionSupervisorUpdate model instance with the provided petition_id and body.
    """
    existing_petition = PetitionManager(db).get_petition(petition_id)
    if not existing_petition:
        raise HTTPException(status_code=404, detail=f"Petition with ID{str(petition_id)} not found")
    return PetitionSupervisorUpdate.model_validate(body, existing_petition)

def get_clerk_petition_update_model(petition_id:UUID, body:dict, db: Session = Depends(get_db)) -> PetitionClerkUpdate:
    """
    Returns a PetitionSupervisorUpdate model instance with the provided petition_id and body.
    """
    existing_petition = PetitionManager(db).get_petition(petition_id)
    if not existing_petition:
        raise HTTPException(status_code=404, detail=f"Petition with ID{str(petition_id)} not found")
    return PetitionClerkUpdate.model_validate(body, existing_petition)