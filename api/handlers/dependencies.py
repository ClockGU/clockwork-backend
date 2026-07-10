from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers.dependencies import get_specified_petition
from api.db.schema import Petition
from api.handlers import PetitionHandler


def get_petition_handler(
    petition: Optional[Petition] = Depends(get_specified_petition),
    db: Session = Depends(get_db),
) -> PetitionHandler:
    """
    Dependency function to provide a PetitionHandler depending on whether a petition was
    specified in the request.
    """
    if petition:
        return PetitionHandler.from_existing_object(db, petition)
    return PetitionHandler(db)
