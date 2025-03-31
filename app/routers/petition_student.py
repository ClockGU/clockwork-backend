from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.handlers.petition_handler import PetitionHandler
from app.pydantic_models.petition import PetitionStudentBase, PetitionStudentUpdate
from app.db.dependencies import get_db
from app.security import get_current_supervisor, get_current_student

router = APIRouter()

## these are the api's fo petitions related to students

def get_petition_handler(
        db: Session = Depends(get_db)
        ) -> PetitionHandler:
    return PetitionHandler(db)

#Api to list all the petitions of students
@router.get("/petitions/students/", response_model=List[PetitionStudentBase])
def read_petitions(
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_student)
):
    petitions = handler.get_student_petitions(user.get('email'))
    return petitions

#Api to upload documents by student
@router.patch("/petitions/students/{petition_id}/upload")
def upload_documents(
    petition_id: UUID,
    peition: PetitionStudentUpdate,
    handler: PetitionHandler = Depends(get_petition_handler),
    user = Depends(get_current_student)
):  
    petition = handler.get_petition(petition_id)
    if not petition:
        raise HTTPException(status_code=404, detail="Petition not found")
    if petition.student_mail != user.get('email'):
        raise HTTPException(status_code=403, detail="You are not authorized to upload documents for this petition")
    
    # here the logic of cCDN will be implemented

    handler.update_petition(petition_id, petition)
    return {"message": "documents uploaded"}