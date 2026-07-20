from datetime import date
from typing import List, Optional, Self
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session

from api.consts import PetitionStatus
from api.db.managers import PetitionManager
from api.db.managers.budget_position_manager import BudgetPositionManager
from api.db.managers.emploeyee_manager import EmployeeManager
from api.db.managers.student_document import StudentDocumentManager
from api.db.schema.petition import Petition
from api.handlers.budget_position_handler import BudgetPositionsHandler
from api.handlers.email_handler import EmailHandler
from api.handlers.exception_handler import ExceptionHandler
from api.pdf.contract import create_contract_pdf
from api.pydantic_models import EmployeeRead, PetitionCreate, PetitionRead
from api.pydantic_models.employee import EmployeeValidate
from api.pydantic_models.petition_update import (
    PetitionSupervisorUpdate,
    PetitionUpdateModel,
)

# TODO: replace the status of petition with enums


class PetitionHandler:

    def __init__(self, db: Session, object_instance: Optional[Petition] = None):
        self.manager = PetitionManager(db)
        self.student_document_manager = StudentDocumentManager(db)
        self.employee_manager = EmployeeManager(db)
        self.db = db
        self.exc = ExceptionHandler()
        self._object_instance = object_instance
        self._budget_positions_handler = (
            BudgetPositionsHandler.from_petition(db, self._object_instance)
            if self._object_instance
            else None
        )

    @property
    def budget_positions_handler(self) -> BudgetPositionsHandler:
        if not self._budget_positions_handler:
            raise RuntimeError(
                "BudgetPositionsHandler is not initialized because no existing petition was provided at initialization."
            )
        return self._budget_positions_handler

    def get_object(self):
        if not self._object_instance:
            raise RuntimeError(
                "Calling get_object() is not allowed when no existing objects was provided at initialization."
            )
        return self._object_instance

    @classmethod
    def from_existing_object(cls, db: Session, object_instance: Petition) -> Self:
        """
        Explicitly create a PetitionHandler instance from an existing Petition object.
        """
        return cls(db, object_instance)

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

    def _send_approval_emails(self, petition: Petition) -> None:
        """Send emails when all budget positions are approved"""
        try:
            email_handler = EmailHandler(petition)

            budget_positions = self.budget_positions_handler.get_objects()

            # Check if student has uploaded documents before sending email
            # TODO: fetching the employee here is not ideal. It is a neccessary fix for now as the signiture of
            #  check_student_documents_uploaded was refactored to require an employee object.
            employee = self.employee_manager.get_employee_by_username(
                petition.student_username
            )
            has_uploaded_documents = (
                self.student_document_manager.check_student_documents_uploaded(
                    employee, check_ba_degree=petition.ba_degree
                )
            )
            # TODO: is_semester_eligible is a built in check that a student may only have one petition going!!! Big issue
            # TODO: is_semeste_eligible should stand for "Send mail that all data is present" aka no more uploads are required.
            is_semester_eligible = self._check_student_semester_eligibility(
                petition.student_username, petition.start_date
            )
            # TODO: send_approval_emails sends a mail to student to provide data,
            #  if he is eligible and has uploaded documents already we send him another mail saying he just needs to approve.
            # Use the existing send_approval_emails method from EmailHandler
            email_handler.send_approval_emails(
                budget_positions, has_uploaded_documents, is_semester_eligible
            )

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

    def _send_revision_request_email(
        self,
        petition: Petition,
        requesting_budget_position,
        message: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> None:
        """Send email when a budget approver requests revision"""
        try:
            email_handler = EmailHandler(petition)
            budget_positions = self.budget_positions_handler.get_objects()

            email_handler.send_revision_request_email(
                requesting_budget_position, budget_positions, message, subject
            )

        except Exception as e:
            self.exc.not_found(f"Error sending revision request email: {str(e)}")

    def _send_rejection_email(
        self, petition: Petition, rejected_budget_position
    ) -> None:
        """Send email when a budget position is rejected"""
        try:
            email_handler = EmailHandler(petition)
            budget_positions = self.budget_positions_handler.get_objects()

            email_handler.send_rejection_email(
                rejected_budget_position, budget_positions
            )

        except Exception as e:
            self.exc.not_found(f"Error sending rejection email: {str(e)}")

    # Method currently not used but possibly needed soon.
    def list_petitions(self, offset: int = 0, limit: int = 100) -> List[Petition]:
        petitions = self.manager.get_petitions(offset=offset, limit=limit)
        if not petitions:
            raise self.exc.not_found("Petitions", message="No petitions found")
        return petitions

    def get_petition(self) -> Petition:
        """
        Get the specified petiition as wrapper for HTTP GET detail endpoint.
        """
        return self.get_object()

    def get_petition_for_approver_action(self, budget_position_id: UUID) -> Petition:
        petition = self.get_object()

        if petition.status != PetitionStatus.APPROVER_ACTION:
            raise self.exc.invalid_status(
                current_status=petition.status,
                required_status=PetitionStatus.APPROVER_ACTION,
            )

        # Check if the budget position is already approved
        budget_position = (
            self.budget_positions_handler.get_assigned_budget_position_by_id(
                budget_position_id
            )
        )

        if budget_position.budget_position_approved:
            raise self.exc.bad_request(
                "This budget position has already been approved by you."
            )

        return petition

    def delete_petition(self) -> dict:
        # Proceed with the deletion
        petition = self.get_object()
        success = self.manager.delete_petition(petition)
        if not success:
            raise self.exc.delete_failed("Petition", str(petition.id))
        return {"detail": "Petition deleted successfully"}

    def delete_petition_as_clerk(self, reason: str = "") -> dict:
        petition = self.get_object()

        # Get budget positions to notify
        budget_positions = self.budget_positions_handler.get_objects()

        # Proceed with the deletion
        success = self.manager.delete_petition(petition)
        if not success:
            raise self.exc.delete_failed("Petition", str(petition.id))

        # Send deletion emails
        email_handler = EmailHandler(petition)
        email_handler.send_clerk_deletion_email(reason, budget_positions)

        return {"detail": "Petition deleted successfully"}

    def get_petitions_by_user(self, user_account: UUID) -> List[Petition]:
        petitions = self.manager.get_petitions_by_user(user_account)
        if not petitions:
            raise self.exc.not_found(
                "Petitions",
                message=f"No petitions found for user with ID {user_account}",
            )
        return petitions

    def get_student_petitions(self, student_username: str) -> List[Petition]:
        petitions = self.manager.get_student_petitions(student_username)
        if not petitions:
            raise self.exc.not_found(
                "Petitions",
                message=f"No petitions found for student username {student_username}",
            )
        return petitions

    def _check_student_semester_eligibility(
        self, student_username: str, start_date: date
    ) -> bool:
        """
        Check if the student is eligible to have a petition in the given semester.
        Returns True if eligible (no approved petition in same semester), False otherwise.
        """
        try:
            existing_petitions = (
                self.manager.get_student_approved_petitions_in_semester(
                    student_username, start_date
                )
            )

            # If there are existing approved petitions in the same semester, student is not eligible
            return len(existing_petitions) != 0

        except Exception as e:
            raise self.exc.internal_error("checking student semester eligibility", e)
            # In case of error, allow the petition (fail-open approach)
            return True

    def student_accept_or_reject_petition(
        self, petition: Petition, approved: bool
    ) -> Petition | dict:
        # Check if student has uploaded documents before approving
        if approved:
            employee = self.employee_manager.get_employee_by_username(
                petition.student_username
            )
            if not employee:
                raise self.exc.bad_request(
                    "You cannot approve the petition unless you are registered as an employee."
                )
            # Validate all fields are populated
            EmployeeValidate.model_validate(employee, from_attributes=True)

            has_uploaded_documents = (
                self.student_document_manager.check_student_documents_uploaded(
                    employee, check_ba_degree=petition.ba_degree
                )
            )
            if not has_uploaded_documents:
                raise self.exc.bad_request(
                    "You cannot approve the petition unless you upload the required documents."
                )
            # Student accepted, move to clerk_action
            petition = self.manager.update_petition_status(
                petition, PetitionStatus.CLERK_ACTION
            )
            # Send email to supervisor
            email_handler = EmailHandler(petition)
            email_handler.send_student_acceptance_email()
        else:
            # Student rejected, notify and then move to clerk_action
            email_handler = EmailHandler(petition)
            email_handler.send_student_rejection_email()

            # Send to budget approvers
            email_handler.send_student_rejection_to_budget_approvers_email(
                petition.budget_positions
            )
            return self.delete_petition()

        return petition

    def approve_petition_as_clerk(self) -> Petition:

        petition = self.get_object()
        budget_positions = self.budget_positions_handler.get_objects()

        try:
            employee = self.employee_manager.get_employee_by_username(
                petition.student_username
            )
            if not employee:
                raise self.exc.not_found("Employee", petition.student_username)

            employee_read = EmployeeRead.model_validate(employee, from_attributes=True)
            petition_read = PetitionRead.model_validate(petition)

            contract_pdf_buffer = create_contract_pdf(employee_read, petition_read)

        except Exception as e:
            raise self.exc.internal_error("creating contract PDF", e)

        try:

            email_handler = EmailHandler(petition)
            email_handler.send_contract_pdf_email(contract_pdf_buffer)
            email_handler.send_clerk_approval_email(budget_positions)

        except Exception as e:
            raise self.exc.internal_error("sending contract PDF", e)

        # Update petition status
        petition = self.manager.update_petition_status(
            petition, PetitionStatus.AWAITING_SIGNATURE
        )

        return petition

    def request_revision_from_student(
        self, petition: Petition, message: str, subject: Optional[str] = None
    ) -> Petition:
        # Send email to student
        email_handler = EmailHandler(petition)
        email_handler.send_clerk_revision_request_email(message, subject)

        # Change status to clerk_revision
        petition = self.manager.update_petition_status(
            petition, PetitionStatus.CLERK_REVISION
        )
        return petition

    def complete_petition_as_clerk(self) -> Petition:

        petition = self.get_object()
        # Send completion emails
        email_handler = EmailHandler(petition)
        email_handler.send_petition_completion_emails()

        # Update petition status to completed
        petition = self.manager.update_petition_status(
            petition, PetitionStatus.COMPLETED
        )

        return petition

    def get_petitions_clerk(self) -> List[Petition]:
        """Return petitions relevant to clerks (several statuses)."""
        statuses = [
            PetitionStatus.AWAITING_SIGNATURE,
            PetitionStatus.COMPLETED,
            PetitionStatus.CLERK_ACTION,
        ]
        return self.manager.get_petitions_by_status(statuses)

    def request_revision_from_supervisor(
        self, petition: Petition, message: str, subject: Optional[str] = None
    ) -> Petition:
        """
        Student requests revision from supervisor.
        Sends email to supervisor and changes status to 'student_revision'.
        """
        email_handler = EmailHandler(petition)
        email_handler.send_student_revision_request_email(message, subject)

        # Update petition status to student_revision
        petition = self.manager.update_petition_status(
            petition, PetitionStatus.STUDENT_REVISION
        )

        return petition

    def update_budget_position_approval(
        self,
        budget_position_id: UUID,
        budget_position_approved: bool,
        message: Optional[str] = None,
        revision_requested: bool = False,
        subject: Optional[str] = None,
    ) -> Petition:
        """Update budget position approval and handle petition status accordingly"""
        try:
            petition = self.get_object()

            # Check if budget position exists and belongs to this petition
            budget_position = (
                self.budget_positions_handler.get_assigned_budget_position_by_id(
                    budget_position_id
                )
            )
            if not budget_position:
                raise self.exc.not_found("Budget position", str(budget_position_id))

            if budget_position.petition_id != petition.id:
                raise self.exc.bad_request(
                    "Budget position does not belong to this petition"
                )

            if budget_position.budget_position_approved:
                raise self.exc.bad_request(
                    "You have already approved this budget position"
                )

            # Update the budget position status
            updated_budget_position = (
                self.budget_positions_handler.update_budget_position_status(
                    budget_position, budget_position_approved
                )
            )

            # Handle different status cases
            if budget_position_approved:
                # Check if all budget positions are now approved
                all_approved = (
                    self.budget_positions_handler.check_all_budget_positions_approved(
                        petition.id
                    )
                )

                if all_approved:
                    petition = self.manager.update_petition_status(
                        petition, PetitionStatus.STUDENT_ACTION
                    )

                    self._send_approval_emails(petition)

            elif revision_requested:
                # Set status to APPROVER_REVISION
                petition = self.manager.update_petition_status(
                    petition, PetitionStatus.APPROVER_REVISION
                )

                self._send_revision_request_email(
                    petition, updated_budget_position, message, subject
                )

            # TODO: This branch is an effective DELETE on the petition. This should be handled by a DELETE endpoint not this patch.
            elif not budget_position_approved and not revision_requested:

                # Send rejection email
                self._send_rejection_email(petition, updated_budget_position)

                self.manager.delete_petition(petition)
                return {"detail": "Petition rejected and deleted successfully"}

            return petition

        except HTTPException as e:
            raise
        except Exception as e:
            raise self.exc.internal_error("updating budget position", e)

    # TODO: untangle the acception from rejection
    def update_petition_as_clerk(self, approved: bool) -> Petition:

        if self.get_object().status == PetitionStatus.CLERK_ACTION:
            return self.approve_petition_as_clerk()
        elif self.get_object().status == PetitionStatus.AWAITING_SIGNATURE and approved:
            return self.complete_petition_as_clerk()
        else:
            raise self.exc.bad_request("Clerk cannot approve or reject at this stage")

    def update_petition_as_supervisor(
        self, petition_data: PetitionUpdateModel
    ) -> Petition:
        petition = self.get_object()
        update_data = petition_data.model_dump(exclude_unset=True)

        budget_positions_updated = update_data.get("budget_positions", None)

        petition = self.manager.update_petition(petition, update_data)
        if not petition:
            raise self.exc.update_failed("Petition", str(petition))

        # Updating a petition as supervisor should reset the approval status of all budget positions.from
        # If budget_positions were in the update data, they were cleared and re-created so no action is needed.
        if not budget_positions_updated:
            self.budget_positions_handler.reset_approval_status()

        petition = self.manager.update_petition_status(
            petition, PetitionStatus.APPROVER_ACTION
        )

        return petition
