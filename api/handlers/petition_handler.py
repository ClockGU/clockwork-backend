from typing import List, Optional
from fastapi import HTTPException
from uuid import UUID
from sqlmodel import Session
from datetime import date

from api.consts import PetitionStatus
from api.db.managers import PetitionManager
from api.db.managers.budget_position_manager import BudgetPositionManager
from api.db.managers.student_document import StudentDocumentManager
from api.db.managers.emploeyee_manager import EmployeeManager
from api.db.schema.petition import Petition
from api.env import settings
from api.handlers.email_handler import EmailHandler
from api.handlers.exception_handler import ExceptionHandler
from api.pydantic_models import (
    EmployeeRead, 
    PetitionRead,
    PetitionCreate
    ) 
from api.pdf.contract import create_contract_pdf


# TODO: replace the status of petition with enums
class PetitionHandler:
    def __init__(self, db: Session):
        self.manager = PetitionManager(db)
        self.budget_position_manager = BudgetPositionManager(db)
        self.student_document_manager = StudentDocumentManager(db)
        self.employee_manager = EmployeeManager(db)
        self.db = db
        self.exc = ExceptionHandler()

    def create_petition(self, petition_data: PetitionCreate) -> Petition:
        try:
            petition = self.manager.create_petition(petition_data)
            if not petition:
                raise self.exc.created_failed("Petition")
                
            # Send notification email to student
            email_handler = EmailHandler(petition)
            email_handler.send_petition_creation_student_email()
            
            return petition
        except Exception as e:
            raise self.exc.internal_error("creating the petition", e)

    def update_budget_position_approval(
            self, petition_id: UUID,
            budget_position_id: UUID,
              budget_position_approved: bool,
              message: Optional[str] = None,
              revision_requested: bool = False,
              rejected: bool = False,
              subject: Optional[str] = None
              ) -> Petition:

        """Update budget position approval and handle petition status accordingly"""
        try:
            petition = self.manager.get_petition(petition_id)
            if not petition:
                raise self.exc.not_found("Petition", str(petition_id))

            # Check if budget position exists and belongs to this petition
            budget_position = self.budget_position_manager.get_budget_position(budget_position_id)
            if not budget_position:
                raise self.exc.not_found("Budget position", str(budget_position_id))
            
            if budget_position.petition_id != petition_id:
                raise self.exc.bad_request("Budget position does not belong to this petition")

            if budget_position.budget_position_approved:
                raise self.exc.bad_request("You have already approved this budget position")
    
            # Update the budget position status
            updated_budget_position = self.budget_position_manager.update_budget_position_status(budget_position_id, budget_position_approved)
            if not updated_budget_position:
                raise self.exc.update_failed("Budget position", message="Failed to update budget position")

            # Handle different status cases
            if budget_position_approved:
                # Check if all budget positions are now approved
                all_approved = self.budget_position_manager.check_all_budget_positions_approved(petition_id)
                
                if all_approved:
                    # Update petition status to student_action using manager
                    petition = self.manager.update_petition_status(petition_id, PetitionStatus.STUDENT_ACTION)
                    
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
                petition = self.manager.update_petition_status(petition_id, PetitionStatus.APPROVER_REVISION)

                #send rejection emails
                self._send_revision_request_email(petition, updated_budget_position, message, subject)

            # Load budget positions
            petition.budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)

            return petition

        except HTTPException as e:
            raise
        except Exception as e:
            raise self.exc.internal_error("updating budget position", e)

    def _send_approval_emails(self, petition: Petition) -> None:
        """Send emails when all budget positions are approved"""
        try:
            email_handler = EmailHandler(petition)
            
            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Check if student has uploaded documents before sending email
            has_uploaded_documents = self.student_document_manager.check_student_documents_uploaded(
                petition.student_username, 
                check_ba_degree=petition.ba_degree
            )
            is_semester_eligible = self._check_student_semester_eligibility(petition.student_username, petition.start_date)

            # Use the existing send_approval_emails method from EmailHandler
            email_handler.send_approval_emails(budget_positions, has_uploaded_documents, is_semester_eligible)

            # If student is eligible and has documents, send acceptance link
            if has_uploaded_documents and is_semester_eligible:
                from api.security import generate_signature
                signature = generate_signature()
                email_handler.send_student_acceptance_link_email(signature)
            else:
                # Send email asking student to upload documents
                email_handler.send_student_documents_upload_request_email()
                
        except Exception as e:
            print(f"Error sending approval emails: {str(e)}", flush=True)

    def _send_revision_request_email(self, petition: Petition, requesting_budget_position, message: Optional[str] = None, subject: Optional[str] = None) -> None:
        """Send email when a budget approver requests revision"""
        try:
            email_handler = EmailHandler(petition)
            
            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            email_handler.send_revision_request_email(requesting_budget_position, budget_positions, message, subject)

        except Exception as e:
            print(f"Error sending revision request email: {str(e)}", flush=True)

    def _send_rejection_email(self, petition: Petition, rejected_budget_position) -> None:
        """Send email when a budget position is rejected"""
        try:
            email_handler = EmailHandler(petition)
            
            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            email_handler.send_rejection_email(rejected_budget_position, budget_positions)

        except Exception as e:
            print(f"Error sending rejection email: {str(e)}", flush=True)

    def list_petitions(self, offset: int = 0, limit: int = 100) -> List[Petition]:
        petitions = self.manager.get_petitions(offset=offset, limit=limit)
        if not petitions:
            raise self.exc.not_found("Petitions", message="No petitions found")
        return petitions

    def get_petition(self, petition_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
        return petition

    def get_petition_for_approver_action(self, petition_id: UUID, budget_position_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
        
        if petition.status != PetitionStatus.APPROVER_ACTION:
             raise self.exc.invalid_status(petition.status, message=f"you have already performed an action")
        
        # Check if the budget position is already approved
        budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)
        for bp in budget_positions:
            if bp.id == budget_position_id and bp.budget_position_approved:
                 raise self.exc.bad_request("This budget position has already been approved")

        return petition

    def update_petition(self, petition_id: UUID, petition_data: PetitionCreate) -> Petition:
        # Check if the petition exists
        existing_petition = self.manager.get_petition(petition_id)
        if not existing_petition:
            raise self.exc.not_found("Petition", str(petition_id))

        if not (existing_petition.status == PetitionStatus.APPROVER_REVISION or existing_petition.status == PetitionStatus.STUDENT_REVISION or existing_petition.status == PetitionStatus.APPROVER_ACTION):
            raise self.exc.forbidden("You don't have permission to update this petition at this stage")
        budget_positions_updated = hasattr(petition_data, 'budget_positions') and petition_data.budget_positions is not None

        # Proceed with the update
        petition = self.manager.update_petition(petition_id, petition_data)
        if not petition:
            raise self.exc.update_failed("Petition", str(petition_id))

        # This makes approved budget positiions unapproved again
        if not budget_positions_updated and petition.status == PetitionStatus.STUDENT_REVISION:
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)
            for budget_position in budget_positions:
                if budget_position.budget_position_approved:
                    self.budget_position_manager.update_budget_position_status(
                        budget_position.id, 
                        False
                    )

        # Send emails to budget approvers if budget positions were updated
        self._send_budget_position_update_emails(petition)

        if petition.status == PetitionStatus.APPROVER_REVISION or petition.status == PetitionStatus.STUDENT_REVISION:
            petition = self.manager.update_petition_status(petition_id, PetitionStatus.APPROVER_ACTION)

        return petition

    def delete_petition(self, petition_id: UUID) -> dict:
        # Check if the petition exists
        existing_petition = self.manager.get_petition(petition_id)
        if not existing_petition:
            raise self.exc.not_found("Petition", str(petition_id))

        # Proceed with the deletion
        success = self.manager.delete_petition(petition_id)
        if not success:
            raise self.exc.delete_failed("Petition", str(petition_id))
        return {"detail": "Petition deleted successfully"}

    def delete_petition_as_clerk(self, petition_id: UUID, reason: str = "") -> dict:
        # Check if the petition exists
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))

        # Get budget positions to notify
        budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)

        # Proceed with the deletion
        success = self.manager.delete_petition(petition_id)
        if not success:
            raise self.exc.delete_failed("Petition", str(petition_id))
            
        # Send deletion emails
        email_handler = EmailHandler(petition)
        email_handler.send_clerk_deletion_email(reason, budget_positions)
        
        return {"detail": "Petition deleted successfully"}

    def get_petitions_by_user(self, user_account: UUID) -> List[Petition]:
        petitions = self.manager.get_petitions_by_user(user_account)
        if not petitions:
            raise self.exc.not_found("Petitions", message=f"No petitions found for user with ID {user_account}")
        return petitions

    def get_student_petitions(self, student_username: str) -> List[Petition]:
        petitions = self.manager.get_student_petitions(student_username)
        if not petitions:
            raise self.exc.not_found("Petitions", message=f"No petitions found for student username {student_username}")
        return petitions

    def get_petitions_by_status(self, status: str) -> List[Petition]:
        petitions = self.manager.get_petitions_by_status(status)
        if not petitions:
            raise self.exc.not_found("Petitions", message=f"No petitions found with status '{status}'")
        return petitions
    
    def check_petition_exists(self, petition_id: UUID) -> None:
        # Check if the petition exists
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
    
    def get_petitions_by_budget_approver(self, budget_approver_email: str) -> List[Petition]:
        petitions = self.manager.get_petitions_by_budget_approver(budget_approver_email)
        if not petitions:
            raise self.exc.not_found("Petitions", message=f"No petitions found for budget approver with email {budget_approver_email}")
        return petitions

    def update_student_petition_status(self, petition_id: UUID, status: str) -> Petition:
        """Update petition status when student accepts or rejects the petition"""
        try:
            # Check if petition exists
            petition = self.manager.get_petition(petition_id)
            if not petition:
                raise self.exc.not_found("Petition", str(petition_id))

            # Check if petition is in the correct status to be updated by student
            if petition.status != PetitionStatus.STUDENT_ACTION:
                raise self.exc.invalid_status(petition.status, PetitionStatus.STUDENT_ACTION, "Petition status must be 'student_action' to be updated by student")
            if status == PetitionStatus.CLERK_ACTION:
                # Check if student has uploaded documents before approving
                employee = self.employee_manager.get_employee_by_username(petition.student_username)
                if not employee:
                    raise self.exc.bad_request("You cannot approve the petition unless you are registered as an employee.")
                if employee.date_of_birth is None or employee.address is None:
                    raise self.exc.bad_request("You cannot approve the petition unless your employee profile is complete (date of birth and address).")
            # Update petition status using manager
            petition = self.manager.update_petition_status(petition_id, status)
            if not petition:
                raise self.exc.update_failed("Petition", message="Failed to update petition status")
            
            # Load budget positions
            petition.budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition_id)
            
            # Send notification emails based on status
            if status == PetitionStatus.CLERK_ACTION:
                self._send_student_acceptance_email(petition)
            elif status == PetitionStatus.REJECTED:
                self._send_student_rejection_email(petition)
            
            return petition

        except HTTPException as e:
            raise
        except Exception as e:
            raise self.exc.internal_error("updating petition status", e)

    def _send_student_acceptance_email(self, petition: Petition) -> None:
        """Send email when student accepts the petition"""
        try:
            email_handler = EmailHandler(petition)
            email_handler.send_student_acceptance_email()
        except Exception as e:
            print(f"Error sending student acceptance email: {str(e)}", flush=True)

    def _send_student_rejection_email(self, petition: Petition) -> None:
        """Send email when student rejects the petition"""
        try:
            email_handler = EmailHandler(petition)
            email_handler.send_student_rejection_email()
        except Exception as e:
            print(f"Error sending student rejection email: {str(e)}", flush=True)

    def _send_budget_position_update_emails(self, petition: Petition) -> None:
        """Send emails to budget approvers when budget positions are updated"""
        try:
            email_handler = EmailHandler(petition)
            
            # Get updated budget positions
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            email_handler.send_budget_position_update_emails(budget_positions)

        except Exception as e:
            raise self.exc.internal_error("sending budget position update emails", e)

    def _check_student_semester_eligibility(self, student_username: str, start_date: date) -> bool:
        """
        Check if student is eligible to have a petition in the given semester.
        Returns True if eligible (no approved petition in same semester), False otherwise.
        """
        try:
            existing_petitions = self.manager.get_student_approved_petitions_in_semester(
                student_username, start_date
            )

            # If there are existing approved petitions in the same semester, student is not eligible
            return len(existing_petitions) != 0

        except Exception as e:
            raise self.exc.internal_error("checking student semester eligibility", e)
            # In case of error, allow the petition (fail-open approach)
            return True

    def _validate_employee_data(self, employee) -> None:
        """
        Validates that the employee has filled out all fields required for the PDF generation.
        Raises HTTPException if any data is missing.
        """
        missing_fields = []

        # List of simple required string/date fields
        required_fields = [
            ("first_name", "Vorname"),
            ("last_name", "Nachname"),
            ("date_of_birth", "Geburtsdatum"),
            ("city_of_birth", "Geburtsort"),
            ("health_insurance", "Krankenkasse"),
            ("nationality", "Staatsangehörigkeit"),
            ("postal_code", "PLZ"),
            ("address", "Adresse"),
            ("user_email", "Email"),
            ("bank_name", "Bank"),
            ("iban", "IBAN"),
            ("bic", "BIC"),
            ("telephone_number", "Telefonnummer"),
            ("gender", "Geschlecht"),
            ("married", "Familienstand"), # boolean, but must be set (not None)
            ("previously_employeed", "Bereits beschäftigt?") # boolean, must be set
        ]

        for field_attr, field_name in required_fields:
            value = getattr(employee, field_attr, None)
            # stricter check: empty strings are not allowed, but False is allowed for booleans
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field_name)

        # Logic for previous employment duration
        # If previously_employeed is True, we must have prev_emp_duration
        if getattr(employee, "previously_employeed", False) is True:
            duration = getattr(employee, "prev_emp_duration", None)
            if not duration or (isinstance(duration, str) and not duration.strip()):
                missing_fields.append("Zeitraum der vorherigen Beschäftigung")

        if missing_fields:
            # Join with comma for readable error message
            missing_str = ", ".join(missing_fields)
            raise HTTPException(
                status_code=400,
                detail=f"Please fill out the following missing fields in your profile: {missing_str}"
            )

    def student_accept_or_reject_petition(self, petition_id: UUID, approved: bool) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
        if petition.status != PetitionStatus.STUDENT_ACTION:
            raise self.exc.bad_request("Student cannot accept or reject at this stage")

        # Check if student has uploaded documents before approving
        if approved:
            employee = self.employee_manager.get_employee_by_username(petition.student_username)
            if not employee:
                raise self.exc.bad_request("You cannot approve the petition unless you are registered as an employee.")
            if employee.date_of_birth is None or employee.address is None:
                raise self.exc.bad_request("You cannot approve the petition unless your employee profile is complete (date of birth and address).")
            has_uploaded_documents = self.student_document_manager.check_student_documents_uploaded(
                petition.student_username, 
                check_ba_degree=petition.ba_degree
            )
            if not has_uploaded_documents:
                raise self.exc.bad_request("You cannot approve the petition unless you upload the required documents.")
            # Student accepted, move to clerk_action
            petition = self.manager.update_petition_status(petition_id, PetitionStatus.CLERK_ACTION)
            # Send email to supervisor
            if petition.supervisor_mail:
                email_handler = EmailHandler(petition)
                email_handler.send_student_acceptance_email()
        else:
            # Student rejected, notify and then move to clerk_action
            petition = self.manager.update_petition_status(petition_id, PetitionStatus.REJECTED)
            email_handler = EmailHandler(petition)
            if petition.supervisor_mail:
                email_handler.send_student_rejection_email()
            
            # Send to budget approvers
            email_handler.send_student_rejection_to_budget_approvers_email(petition.budget_positions)
            
        return petition
    
    def update_petition_as_clerk(self, petition_id: UUID, approved: bool) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))

        if petition.status == PetitionStatus.CLERK_ACTION:
            return self.approve_petition_as_clerk(petition_id, approved)
        elif petition.status == PetitionStatus.AWAITING_SIGNATURE and approved:
            return self.complete_petition_as_clerk(petition_id)
        else:
            raise self.exc.bad_request("Clerk cannot approve or reject at this stage")
        

    def approve_petition_as_clerk(self, petition_id: UUID, approved: bool) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
        if petition.status != PetitionStatus.CLERK_ACTION:
            raise self.exc.bad_request("Clerk cannot approve or reject at this stage")
        

        # Update petition status
        petition = self.manager.update_petition_status(petition_id, PetitionStatus.AWAITING_SIGNATURE if approved else PetitionStatus.REJECTED)
        
        email_handler = EmailHandler(petition)
        budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)
        email_handler.send_clerk_approval_email(approved, budget_positions)
        
        if approved:
            # Create contract PDF and email it to the employee (and student)
            try:
                employee = self.employee_manager.get_employee_by_username(petition.student_username)
                if not employee:
                    raise self.exc.not_found("Employee", petition.student_username)
                    
                employee_read = EmployeeRead.model_validate(employee, from_attributes=True)
                petition_read = PetitionRead.model_validate(petition)
                
                contract_pdf_buffer = create_contract_pdf(employee_read, petition_read)
                
                # Send contract PDF via email
                email_handler.send_contract_pdf_email(contract_pdf_buffer)
                        
            except Exception as e:
                raise self.exc.internal_error("creating/sending contract PDF", e)

        return petition

    def request_revision_from_student(self, petition_id: UUID, message: str, subject: Optional[str] = None) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
        if petition.status != PetitionStatus.CLERK_ACTION:
            raise self.exc.invalid_status(PetitionStatus.CLERK_ACTION, message="Revision can only be requested when petition status is 'clerk_action'")

        # Send email to student
        email_handler = EmailHandler(petition)
        email_handler.send_clerk_revision_request_email(message, subject)
        
        # Change status to clerk_revision
        petition = self.manager.update_petition_status(petition_id, PetitionStatus.CLERK_REVISION)
        return petition

    def complete_petition_as_clerk(self, petition_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
        if petition.status != PetitionStatus.AWAITING_SIGNATURE:
            raise self.exc.invalid_status(PetitionStatus.AWAITING_SIGNATURE, message="Petition can only be completed when status is 'awaiting_signature'")

        # Update petition status to completed
        petition = self.manager.update_petition_status(petition_id, PetitionStatus.COMPLETED)
        
        # Send completion emails
        email_handler = EmailHandler(petition)
        email_handler.send_petition_completion_emails()
        
        return petition

    def get_petitions_clerk(self) -> List[Petition]:
        """Return petitions relevant to clerks (several statuses)."""
        try:
            statuses = [PetitionStatus.AWAITING_SIGNATURE, PetitionStatus.COMPLETED, PetitionStatus.CLERK_REVISION, PetitionStatus.CLERK_ACTION]
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
        except HTTPException as e:
            raise
        except Exception as e:
            raise self.exc.internal_error("fetching clerk petitions", e)

    def mark_revision_done_student(self, petition_id: UUID) -> Petition:
        petition = self.manager.get_petition(petition_id)
        
        if not petition:
            raise self.exc.not_found("Petition", str(petition_id))
        if petition.status != PetitionStatus.CLERK_REVISION:
            raise self.exc.invalid_status(PetitionStatus.CLERK_REVISION, message="Revision can only be marked done when petition status is clerk_revision")

        # Change status back to clerk_action
        petition = self.manager.update_petition_status(petition_id, PetitionStatus.CLERK_ACTION)

        return petition

    def request_revision_from_supervisor(self, petition_id: UUID, text: str, subject: Optional[str] = None) -> Petition:
        """
        Student requests revision from supervisor.
        Sends email to supervisor and changes status to 'student_revision'.
        """
        try:
            # Get petition
            petition = self.manager.get_petition(petition_id)
            if not petition:
                raise self.exc.not_found("Petition", str(petition_id))
            
            # Check if petition is in a valid status for student to request revision
            # Students can request revision when petition is in student_action, clerk_revision, or awaiting_signature
            valid_statuses = [PetitionStatus.STUDENT_ACTION, PetitionStatus.CLERK_REVISION]
            if petition.status not in valid_statuses:
                raise self.exc.invalid_status(petition.status, message=f"Student cannot request revision at this stage. Current status: {petition.status}")
            
            # Send email to supervisor using EmailHandler
            if petition.supervisor_mail:
                email_handler = EmailHandler(petition)
                email_handler.send_student_revision_request_email(text, subject)

            # Update petition status to student_revision
            petition = self.manager.update_petition_status(petition_id, PetitionStatus.STUDENT_REVISION)
            if not petition:
                raise self.exc.update_failed("Petition", message="Failed to update petition status")
            
            return petition
            
        except HTTPException as e:
            raise
        except Exception as e:
            raise self.exc.internal_error("requesting revision", e)
