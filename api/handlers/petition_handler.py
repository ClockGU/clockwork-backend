from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from fastapi import HTTPException
from datetime import date

from api.db.managers import PetitionManager
from api.db.managers.budget_position_manager import BudgetPositionManager
from api.db.managers.student_document import StudentDocumentManager
from api.db.managers.emploeyee_manager import EmployeeManager
from api.db.schema.petition import Petition  
from api.handlers.email_handler import EmailHandler
from api.pydantic_models import (
    EmployeeRead, 
    PetitionRead,
    PetitionCreate
    ) 
from api.pdf.contract import create_contract_pdf



class PetitionHandler:
    def __init__(self, db: Session):
        self.manager = PetitionManager(db)
        self.budget_position_manager = BudgetPositionManager(db)
        self.student_document_manager = StudentDocumentManager(db)
        self.employee_manager = EmployeeManager(db)
        self.email_handler = EmailHandler()

    def create_petition(self, petition_data: PetitionCreate) -> Petition:
        try:
            petition = self.manager.create_petition(petition_data)
            if not petition:
                raise HTTPException(status_code=400, detail="Petition could not be created")
            return petition
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while creating the petition: {str(e)}")

    def update_budget_position_approval(
            self, petition_id: UUID,
            budget_position_id: UUID,
              budget_position_approved: bool,
              message: Optional[str] = None,
              revision_requested: bool = False,
              rejected: bool = False
              ) -> Petition:

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

            # Update the budget position status
            updated_budget_position = self.budget_position_manager.update_budget_position_status(budget_position_id, budget_position_approved)
            if not updated_budget_position:
                raise HTTPException(status_code=400, detail="Failed to update budget position")

            # Handle different status cases
            if budget_position_approved:
                # Check if all budget positions are now approved
                all_approved = self.budget_position_manager.check_all_budget_positions_approved(petition_id)
                
                if all_approved:
                    # Update petition status to student_action using manager
                    petition = self.manager.update_petition_status(petition_id, "student_action")
                    
                    # Send approval emails
                    self._send_approval_emails(petition)

            elif not budget_position_approved and not revision_requested:
                
                # Send rejection email
                self._send_rejection_email(petition, updated_budget_position)

                deleted = self.manager.delete_petition(petition_id)
                return {"detail": "Petition rejected and deleted successfully"}


            elif revision_requested:
                # Budget approver wants revision - keep petition status as pending
                # Send revision request email
                petition = self.manager.update_petition_status(petition_id, "approver_revision")

                #send rejection emails
                self._send_revision_request_email(petition, updated_budget_position, message)

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

            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Send email to all budget approvers notifying them that petition is fully approved
            for budget_position in budget_positions:
                self.email_handler.send_email(
                    recipient=budget_position.budget_approver,
                    subject="Petition Fully Approved - Awaiting Student Action",
                    body=f"Petition {petition.id} has been approved by all budget approvers, including yourself. "
                         f"Your budget position '{budget_position.budget_position}' was approved. "
                         f"The petition is now awaiting student action."
                )

            # Check if student has uploaded documents before sending email
            has_uploaded_documents = self.student_document_manager.check_student_documents_uploaded(petition.student_mail)
            is_semester_eligible = self._check_student_semester_eligibility(petition.student_mail, petition.start_date)

            if has_uploaded_documents and is_semester_eligible:
                # Generate signature for the petition acceptance link
                from api.security import generate_signature
                signature = generate_signature()
                petition_url = f"https://preview.clock.uni-frankfurt.de/student/accept?petition_id={petition.id}&signature={signature}"
                
                # Send email to student with acceptance link
                self.email_handler.send_email(
                    recipient=petition.student_mail,
                    subject="New petition requires your acceptance",
                    body=f"A new petition has been created and approved for you. Your documents have already been verified. "
                         f"Please click the following link to review and accept the petition: {petition_url}"
                )

            else:
                # Send email asking student to upload documents
                self.email_handler.send_email(
                    recipient=petition.student_mail,
                    subject="Upload Documents Required",
                    body=f"Your petition has been approved. Please upload the required documents (Elstam, Studienbescheinigung, Versicherungsbescheinigung) to complete your petition."
                )
                
        except Exception as e:
            print(f"Error sending approval emails: {str(e)}", flush=True)

    def _send_revision_request_email(self, petition: Petition, requesting_budget_position, message: Optional[str] = None) -> None:
        """Send email when a budget approver requests revision"""
        try:
            revision_message = message if message else "No specific message provided."

            # Send email to supervisor
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="Petition Revision Requested",
                    body=f"Budget approver {requesting_budget_position.budget_approver} for budget position "
                         f"'{requesting_budget_position.budget_position}' has requested a revision for petition {petition.id}.\n\n"
                         f"Message: {revision_message}"
                )

            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Send email to all other budget approvers
            for budget_position in budget_positions:
                if budget_position.id != requesting_budget_position.id:
                    self.email_handler.send_email(
                        recipient=budget_position.budget_approver,
                        subject="Petition Revision Requested by Another Approver",
                        body=f"Budget approver {requesting_budget_position.budget_approver} has requested a revision "
                             f"for petition {petition.id} (budget position: '{requesting_budget_position.budget_position}').\n\n"
                             f"Message: {revision_message}\n\n"
                             f"You may need to review your approval for budget position '{budget_position.budget_position}'."
                    )

        except Exception as e:
            print(f"Error sending revision request email: {str(e)}", flush=True)

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

            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Send email to all budget approvers (approved or not)
            for budget_position in budget_positions:
                if budget_position.id != rejected_budget_position.id:
                    self.email_handler.send_email(
                        recipient=budget_position.budget_approver,
                        subject="Petition Rejected by Another Approver",
                        body=f"Petition {petition.id} has been rejected by budget approver {rejected_budget_position.budget_approver} "
                             f"for budget position '{rejected_budget_position.budget_position}'. "
                             f"Your review for budget position '{budget_position.budget_position}' is no longer needed."
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

        if not (existing_petition.status == "approver_revision" or existing_petition.status == "student_revision" or existing_petition.status == "approver_action"):
            raise HTTPException(
                status_code=400, 
                detail=f"you don't have permission to update this petition at this stage"
            )
        budget_positions_updated = hasattr(petition_data, 'budget_positions') and petition_data.budget_positions is not None

        # Proceed with the update
        petition = self.manager.update_petition(petition_id, petition_data)
        if not petition:
            raise HTTPException(status_code=400, detail=f"Petition with ID {petition_id} could not be updated")

        # This makes approved budget positiions unapproved again
        if not budget_positions_updated and petition.status == "student_revision":
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)
            for budget_position in budget_positions:
                if budget_position.budget_position_approved:
                    self.budget_position_manager.update_budget_position_status(
                        budget_position.id, 
                        False
                    )

        # Send emails to budget approvers if budget positions were updated
        self._send_budget_position_update_emails(petition)

        if petition.status == "approver_revision" or petition.status == "student_revision":
            petition = self.manager.update_petition_status(petition_id, "approver_action")

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

    def update_student_petition_status(self, petition_id: UUID, status: str) -> Petition:
        """Update petition status when student accepts or rejects the petition"""
        try:
            # Check if petition exists
            petition = self.manager.get_petition(petition_id)
            if not petition:
                raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")

            # Check if petition is in the correct status to be updated by student
            if petition.status != "student_action":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Petition status is '{petition.status}', but must be 'student_action' to be updated by student"
                )
            if status == "clerk_action":
                # Check if student has uploaded documents before approving
                employee = self.employee_manager.get_employee_by_email(petition.student_mail)
                if not employee:
                    raise HTTPException(
                        status_code=400,
                        detail="You cannot approve the petition unless you are registered as an employee."
                    )
                if employee.date_of_birth is None or employee.address is None:
                    raise HTTPException(
                        status_code=400,
                        detail="You cannot approve the petition unless your employee profile is complete (date of birth and address)."
                    )
            # Update petition status using manager
            petition = self.manager.update_petition_status(petition_id, status)
            if not petition:
                raise HTTPException(status_code=400, detail="Failed to update petition status")
            
            # Load budget positions
            petition.budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)
            
            # Send notification emails based on status
            if status == "clerk_action":
                self._send_student_acceptance_email(petition)
            elif status == "rejected":
                self._send_student_rejection_email(petition)
            
            return petition

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while updating petition status: {str(e)}")

    def _send_student_acceptance_email(self, petition: Petition) -> None:
        """Send email when student accepts the petition"""
        try:
            # Send email to supervisor
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="Student Accepted Petition",
                    body=f"Student has accepted petition {petition.id}. The petition is now ready for clerk review."
                )
        except Exception as e:
            print(f"Error sending student acceptance email: {str(e)}", flush=True)

    def _send_student_rejection_email(self, petition: Petition) -> None:
        """Send email when student rejects the petition"""
        try:
            # Send email to supervisor
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="Student Rejected Petition",
                    body=f"Student has rejected petition {petition.id}. Please review the petition details."
                )
        except Exception as e:
            print(f"Error sending student rejection email: {str(e)}", flush=True)

    def _send_budget_position_update_emails(self, petition: Petition) -> None:
        """Send emails to budget approvers when budget positions are updated"""
        try:
            # due to circular import this is imported here
            from api.security import generate_signature
            signature = generate_signature()

            # Get updated budget positions
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Send email to all budget approvers with updated budget positions
            for budget_position in budget_positions:
                petition_url = f"https://preview.clock.uni-frankfurt.de/approver?petition_id={petition.id}&signature={signature}&budget_position_id={budget_position.id}"

                self.email_handler.send_email(
                    recipient=budget_position.budget_approver,
                    subject="Petition Updated - Action Required",
                    body=f"The petition with id {petition.id} have been updated. "
                         f"Your budget position '{budget_position.budget_position}' requires re-approval. "
                         f"Please review and approve the updated petition: {petition_url}"
                )

            print(f"Budget position update emails sent for petition {petition.id}", flush=True)

        except Exception as e:
            print(f"Error sending budget position update emails: {str(e)}", flush=True)

    def _check_student_semester_eligibility(self, student_email: str, start_date: date) -> bool:
        """
        Check if student is eligible to have a petition in the given semester.
        Returns True if eligible (no approved petition in same semester), False otherwise.
        """
        try:
            existing_petitions = self.manager.get_student_approved_petitions_in_semester(
                student_email, start_date
            )

            # If there are existing approved petitions in the same semester, student is not eligible
            return len(existing_petitions) != 0

        except Exception as e:
            print(f"Error checking student semester eligibility: {str(e)}", flush=True)
            # In case of error, allow the petition (fail-open approach)
            return True

    def student_accept_or_reject_petition(self, petition_id: UUID, approved: bool) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        if petition.status != "student_action":
            raise HTTPException(status_code=400, detail="Student cannot accept or reject at this stage")

        # Check if student has uploaded documents before approving
        if approved:
            employee = self.employee_manager.get_employee_by_email(petition.student_mail)
            if not employee:
                raise HTTPException(
                    status_code=400,
                    detail="You cannot approve the petition unless you are registered as an employee."
                )
            if employee.date_of_birth is None or employee.address is None:
                raise HTTPException(
                    status_code=400,
                    detail="You cannot approve the petition unless your employee profile is complete (date of birth and address)."
                )
            has_uploaded_documents = self.student_document_manager.check_student_documents_uploaded(petition.student_mail)
            if not has_uploaded_documents:
                raise HTTPException(
                    status_code=400,
                    detail="You cannot approve the petition unless you upload the required documents."
                )
            # Student accepted, move to clerk_action
            petition = self.manager.update_petition_status(petition_id, "clerk_action")
            # Send email to supervisor
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="Student Accepted Petition",
                    body=f"Student has accepted petition {petition.id}. The petition is now ready for clerk review."
                )
        else:
            # Student rejected, notify and then move to clerk_action
            petition = self.manager.update_petition_status(petition_id, "rejected")
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="Student Rejected Petition",
                    body=f"Student has rejected petition {petition.id}. Please review the petition details."
                )
            for budget_position in petition.budget_positions:
                self.email_handler.send_email(
                    recipient=budget_position.budget_approver,
                    subject="Petition Rejected by Student",
                    body=f"Petition {petition.id} was rejected by the student."
                )
        return petition
    
    def update_petition_as_clerk(self, petition_id: UUID, approved: bool) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        if petition.status == "clerk_action":
            return self.approve_petition_as_clerk(petition_id, approved)
        elif petition.status == "awaiting_signature" and approved:
            return self.complete_petition_as_clerk(petition_id)
        else:
            raise HTTPException(status_code=400, detail="Clerk cannot approve or reject at this stage")
        

    def approve_petition_as_clerk(self, petition_id: UUID, approved: bool) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        if petition.status != "clerk_action":
            raise HTTPException(status_code=400, detail="Clerk cannot approve or reject at this stage")
        

        # Update petition status
        petition = self.manager.update_petition_status(petition_id, "awaiting_signature" if approved else "rejected")
        if petition.supervisor_mail:
            self.email_handler.send_email(
                recipient=petition.supervisor_mail,
                subject="Clerk Updated Petition Status",
                body=f"Clerk has {'approved' if approved else 'rejected'} petition {petition.id}. Please review the petition details."
            )
        for budget_position in petition.budget_positions:
            self.email_handler.send_email(
                recipient=budget_position.budget_approver,
                subject="Petition Status Updated by Clerk",
                body=f"Petition {petition.id} was {'approved' if approved else 'rejected'} by the clerk."
            )
        
        if approved:
            # Create contract PDF and email it to the employee (and student)
            try:
                employee = self.employee_manager.get_employee_by_email(petition.student_mail)
                if employee:
                    employee_read = EmployeeRead.model_validate(employee,from_attributes=True)
                    petition_read = PetitionRead.model_validate(petition, from_attributes=True)

                    # Create PDF bytes
                    pdf_buf = create_contract_pdf(employee_read, petition_read)
                    pdf_bytes = pdf_buf.getvalue()
                    filename = f"Arbeitsvertrag_{employee.last_name}_{employee.first_name}_{date.today().strftime('%d-%m-%Y')}.pdf"

                    # Send to employee
                    if employee.user_email:
                        self.email_handler.send_email(
                            recipient=employee.user_email,
                            subject="Your Employment Contract",
                            body=f"Dear {employee.first_name or ''},\n\nPlease find attached your employment contract for petition {petition.id}. Please print it out twice and handover the signed version",
                            attachment_bytes=pdf_bytes,
                            attachment_filename=filename,
                        )
                        
            except Exception as e:
                print(f"Failed to create/send contract: {e}", flush=True)

        return petition

    def request_revision_from_student(self, petition_id: UUID, message: str) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        if petition.status != "clerk_action":
            raise HTTPException(status_code=400, detail="Revision can only be requested when petition status is 'clerk_action'")

        # Send email to student
        self.email_handler.send_email(
            recipient=petition.student_mail,
            subject="Revision Requested for Your Petition",
            body=f"The clerk has requested a revision for your petition.\n\nMessage: {message}"
        )
        # Change status to clerk_revision
        petition = self.manager.update_petition_status(petition_id, "clerk_revision")
        return petition

    def complete_petition_as_clerk(self, petition_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        if petition.status != "awaiting_signature":
            raise HTTPException(status_code=400, detail="Petition can only be completed when status is 'awaiting_signature'")

        # Update petition status to completed
        petition = self.manager.update_petition_status(petition_id, "completed")
        
        # Send email to student
        self.email_handler.send_email(
            recipient=petition.student_mail,
            subject="Your Petition is Completed",
            body=f"Your petition {petition.id} has been completed. Welcome aboard!"
        )
        self.email_handler.send_email(
            recipient=petition.supervisor_mail,
            subject="Petition Completed",
            body=f"Petition {petition.id} has been completed for the student. All steps are finalized."
        )
        return petition

    def get_petitions_clerk(self) -> List[Petition]:
        """Return petitions relevant to clerks (several statuses)."""
        try:
            statuses = ["awaiting_signature", "completed", "clerk_revision", "clerk_action"]
            petitions = []
            for s in statuses:
                # call manager directly to avoid raising on empty per-status result
                res = self.manager.get_petitions_by_status(s)
                if res:
                    petitions.extend(res)

            # dedupe by id
            seen = set()
            unique = []
            for p in petitions:
                if getattr(p, "id", None) not in seen:
                    seen.add(p.id)
                    unique.append(p)

            if not unique:
                return []

            return unique
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while fetching clerk petitions: {str(e)}")

    def mark_revision_done_student(self, petition_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        
        if not petition:
            raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
        if petition.status != "clerk_revision":
            raise HTTPException(status_code=400, detail="Revision can only be marked done when petition status is clerk_revision")

        # Change status back to clerk_action
        petition = self.manager.update_petition_status(petition_id, "clerk_action")

        return petition

    def request_revision_from_supervisor(self, petition_id: UUID, text: str) -> Petition:
        """
        Student requests revision from supervisor.
        Sends email to supervisor and changes status to 'student_revision'.
        """
        try:
            # Get petition
            petition = self.manager.get_petition(petition_id)
            if not petition:
                raise HTTPException(status_code=404, detail=f"Petition with ID {petition_id} not found")
            
            # Check if petition is in a valid status for student to request revision
            # Students can request revision when petition is in student_action, clerk_revision, or awaiting_signature
            valid_statuses = ["student_action", "clerk_revision"]
            if petition.status not in valid_statuses:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Student cannot request revision at this stage. Current status: {petition.status}"
                )
            
            # Send email to supervisor
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject=f"Revision Requested by Student for Petition {petition_id}",
                    body=f"The student has requested a revision for petition {petition_id}.\n\n"
                         f"Student email: {petition.student_mail}\n"
                         f"Revision request message:\n{text}\n\n"
                         f"Please review and make necessary changes to the petition."
                )
            
            # Update petition status to student_revision
            petition = self.manager.update_petition_status(petition_id, "student_revision")
            if not petition:
                raise HTTPException(status_code=400, detail="Failed to update petition status")
            
            return petition
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"An error occurred while requesting revision: {str(e)}"
            )