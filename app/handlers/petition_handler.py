from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from fastapi import HTTPException

from app.db.managers import PetitionManager
from app.db.managers.budget_position_manager import BudgetPositionManager
from app.pydantic_models.petition import PetitionCreate  # Pydantic model for input
from app.db.schema.petition import Petition  # ORM model
from app.handlers.email_handler import EmailHandler


class PetitionHandler:
    def __init__(self, db: Session):
        self.manager = PetitionManager(db)
        self.budget_position_manager = BudgetPositionManager(db)
        self.email_handler = EmailHandler()

    def create_petition(self, petition_data: PetitionCreate) -> Petition:
        try:
            petition = self.manager.create_petition(petition_data)
            if not petition:
                raise HTTPException(status_code=400, detail="Petition could not be created")
            return petition
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while creating the petition: {str(e)}")

    def update_budget_position_approval(self, petition_id: UUID, budget_position_id: UUID, budget_approved: bool) -> Petition:
        """Update budget position approval and handle petition status accordingly"""
        try:
            petition = self.manager.get_petition(petition_id)
            if not petition:
                raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")

            # Check if budget position exists and belongs to this petition
            budget_position = self.budget_position_manager.get_budget_position(budget_position_id)
            if not budget_position:
                raise HTTPException(status_code=404, detail=f"Budget position with ID {budget_position_id} not found")
            
            if budget_position.petition_id != petition_id:
                raise HTTPException(status_code=400, detail="Budget position does not belong to this petition")

            # Update the budget position approval status
            updated_budget_position = self.budget_position_manager.update_budget_position(budget_position_id, budget_approved)
            if not updated_budget_position:
                raise HTTPException(status_code=400, detail="Failed to update budget position")

            # Handle approval logic
            if budget_approved:
                # Check if all budget positions are now approved
                all_approved = self.budget_position_manager.check_all_budget_positions_approved(petition_id)
                
                if all_approved:
                    # Update petition status to student_action
                    petition.status = "student_action"
                    self.manager.db.add(petition)
                    self.manager.db.commit()
                    
                    # Send approval emails
                    self._send_approval_emails(petition)
                    
            else:
                # Budget position rejected - update petition status to rejected
                petition.status = "rejected"
                self.manager.db.add(petition)
                self.manager.db.commit()
                
                # Send rejection email
                self._send_rejection_email(petition, updated_budget_position)

            # Refresh petition to get updated data
            self.manager.db.refresh(petition)
            
            # Load budget positions
            petition.budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)
            
            return petition

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while updating budget position: {str(e)}")

    def _send_approval_emails(self, petition: Petition) -> None:
        """Send emails when all budget positions are approved"""
        try:
            # Send email to supervisor
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="Petition Approved",
                    body=f"Petition {petition.id} has been approved by all budget approvers."
                )
            
            # Send email to student
            self.email_handler.send_email(
                recipient=petition.student_mail,
                subject="Upload Documents",
                body=f"Your petition has been approved. Please upload the required documents for your petition."
            )
        except Exception as e:
            print(f"Error sending approval emails: {str(e)}", flush=True)

    def _send_rejection_email(self, petition: Petition, rejected_budget_position) -> None:
        """Send email when a budget position is rejected"""
        try:
            # Send email to supervisor
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="Petition Rejected",
                    body=f"Petition {petition.id} has been rejected due to budget position '{rejected_budget_position.budget_position}' being denied by {rejected_budget_position.budget_approver}."
                )
        except Exception as e:
            print(f"Error sending rejection email: {str(e)}", flush=True)

    def list_petitions(self, offset: int = 0, limit: int = 100) -> List[Petition]:
        petitions = self.manager.get_petitions(offset=offset, limit=limit)
        if not petitions:
            raise HTTPException(status_code=404, detail="No petitions found")
        return petitions

    def get_petition(self, petition_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        return petition

    def update_petition(self, petition_id: UUID, petition_data: PetitionCreate) -> Petition:
        # Check if the petition exists
        existing_petition = self.manager.get_petition(petition_id)
        if not existing_petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")

        # Proceed with the update
        petition = self.manager.update_petition(petition_id, petition_data)
        if not petition:
            raise HTTPException(status_code=400, detail=f"Petition with ID {petition_id} could not be updated")
        return petition

    def delete_petition(self, petition_id: UUID) -> dict:
        # Check if the petition exists
        existing_petition = self.manager.get_petition(petition_id)
        if not existing_petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")

        # Proceed with the deletion
        success = self.manager.delete_petition(petition_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Petition with ID {petition_id} could not be deleted")
        return {"detail": "Petition deleted successfully"}

    def get_petitions_by_user(self, user_account: UUID) -> List[Petition]:
        petitions = self.manager.get_petitions_by_user(user_account)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found for user with ID {user_account}")
        return petitions

    def get_student_petitions(self, student_mail: str) -> List[Petition]:
        petitions = self.manager.get_student_petitions(student_mail)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found for student with email {student_mail}")
        return petitions

    def get_petitions_by_status(self, status: str) -> List[Petition]:
        petitions = self.manager.get_petitions_by_status(status)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found with status '{status}'")
        return petitions
    
    def check_petition_exists(self, petition_id: UUID) -> None:
        # Check if the petition exists
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
    
    def get_petitions_by_budget_approver(self, budget_approver_email: str) -> List[Petition]:
        petitions = self.manager.get_petitions_by_budget_approver(budget_approver_email)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found for budget approver with email {budget_approver_email}")
        return petitions


