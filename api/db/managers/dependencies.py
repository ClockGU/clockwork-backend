from uuid import UUID

from fastapi import Depends, HTTPException
from sqlmodel import Session

from api.db.dependencies import get_db
from api.db.managers import PetitionManager
from api.db.schema import Petition


def get_specified_petition(
    petition_id: UUID, db: Session = Depends(get_db)
) -> Petition:
    existing_petition = PetitionManager(db).get_petition(petition_id)
    if not existing_petition:
        raise HTTPException(
            status_code=404, detail=f"Petition with ID{str(petition_id)} not found"
        )
    return existing_petition
