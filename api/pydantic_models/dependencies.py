from fastapi import Depends
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import get_specified_petition
from api.db.schema import Petition
from api.pydantic_models import PetitionSupervisorUpdate, PetitionClerkUpdate


def get_supervisor_petition_update_model(body:dict, petition: Petition = Depends(get_specified_petition), db: Session = Depends(get_db)) -> PetitionSupervisorUpdate:
    """
    Returns a PetitionSupervisorUpdate model instance with the provided petition_id and body.
    """
    return PetitionSupervisorUpdate.model_validate(body, petition)

def get_clerk_petition_update_model(body:dict, petition: Petition = Depends(get_specified_petition), db: Session = Depends(get_db)) -> PetitionClerkUpdate:
    """
    Returns a PetitionSupervisorUpdate model instance with the provided petition_id and body.
    """
    return PetitionClerkUpdate.model_validate(body, petition)