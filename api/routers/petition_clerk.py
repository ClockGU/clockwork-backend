from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session
from starlette.responses import StreamingResponse

from api.consts import PetitionStatus
from api.db.dependencies import get_db
from api.db.managers.dependencies import get_specified_petition
from api.db.managers.emploeyee_manager import EmployeeManager
from api.db.schema import Petition
from api.handlers import EmployeeHandler
from api.handlers.dependencies import get_petition_handler
from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import (
    ClerkDeletionRequest,
    ClerkRevisionRequest,
    PetitionClerkUpdate,
    PetitionRead,
)
from api.pydantic_models.dependencies import get_clerk_petition_update_model
from api.security import get_current_clerk
from api.websockets.routers.web_socket import send_serialized_data_to_clerks

router = APIRouter()


# 2. API to delete a petition by ID
@router.delete("/clerk/petitions/{petition_id}")
async def delete_petition(
    petition: Petition = Depends(get_specified_petition),
    deletion_request: ClerkDeletionRequest = Body(
        default=ClerkDeletionRequest(reason="")
    ),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk),
):
    success = handler.delete_petition_as_clerk(petition, deletion_request.reason)
    await send_serialized_data_to_clerks(
        [
            petition.dict(by_alias=True, exclude_none=True)
            for petition in handler.get_petitions_clerk()
        ]
    )
    return success


# 3. API to update a petition
@router.patch("/clerk/petitions/{petition_id}", response_model=PetitionRead)
async def update_petition_as_clerk(
    petition: Petition = Depends(get_specified_petition),
    petition_data: PetitionClerkUpdate = Depends(get_clerk_petition_update_model),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk),
):
    updated_petition = handler.update_petition_as_clerk(approved=petition_data.approved)

    # TODO: Get rid of this part after reassuring that the frontend does not use it.
    if updated_petition.status == "rejected":
        return handler.delete_petition(petition)

    return updated_petition


@router.patch(
    "/clerk/petitions/{petition_id}/request-revision", response_model=PetitionRead
)
async def request_revision_from_student(
    petition: Petition = Depends(get_specified_petition),
    revision: ClerkRevisionRequest = Body(...),
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk),
):
    updated_petition = handler.request_revision_from_student(
        petition=petition, message=revision.message, subject=revision.subject
    )
    return updated_petition


@router.get("/clerk/petitions/{petition_id}/student-data-pdf")
async def get_student_data_pdf(
    handler: PetitionHandler = Depends(get_petition_handler),
    user=Depends(get_current_clerk),
):
    petition = handler.get_object()
    employee = EmployeeManager(handler.db).get_employee_by_username(
        petition.student_username
    )
    employee_handler = EmployeeHandler.from_existing_object(handler.db, employee)
    pdf_buffer = employee_handler.get_student_data_pdf()

    filename = f"Student_Data_{employee.last_name}_{employee.first_name}_{date.today().strftime('%d-%m-%Y')}.pdf"

    # Return as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
