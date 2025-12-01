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
from api.env import settings
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
                    subject="[ClockWork] Kostenstellen freigegeben / Budget approved", 
                    body=f"Ihr Antrag {petition.id} für die Einstellung einer studentischen Hilfskraft wurde von allen Kostenstellenverantwortlichen freigegeben."
                    f"\n\n--------------\n\n"
                    f"Your application {petition.id} for the employment of a new student assistant has been approved by all budget approvers."
                )

            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Send email to all budget approvers notifying them that petition is fully approved
            for budget_position in budget_positions:
                self.email_handler.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Kostenstellen freigegeben / Budget approved", 
                    body=f"Der Antrag {petition.id} für die Einstellung einer studentischen Hilfskraft wurde von allen Kostenstellenverantwortlichen freigegeben."
                    f"\n\n--------------\n\n"
                    f"The application {petition.id} for the employment of a new student assistant has been approved by all budget approvers."
                )

            # Check if student has uploaded documents before sending email
            has_uploaded_documents = self.student_document_manager.check_student_documents_uploaded(petition.student_username)
            is_semester_eligible = self._check_student_semester_eligibility(petition.student_username, petition.start_date)

            if has_uploaded_documents and is_semester_eligible:
                # Generate signature for the petition acceptance link
                from api.security import generate_signature
                signature = generate_signature()
                petition_url = f"{settings.FRONTEND_URL}/student/accept?petition_id={petition.id}&signature={signature}"
                
                # Send email to student with acceptance link
                self.email_handler.send_email(
                    recipient=petition.student_mail,
                    subject="[ClockWork] Einstellung als studentische Hilfskraft / Employment as a student assistant",
                    body=f"Für Sie wurde ein Antrag zur Einstellung als studentische Hilfskraft gestellt.\n\n"
                    f"Bitte nutzen Sie den folgenden Link, um sich anzumelden und dem Antrag zuzustimmen: {petition_url}"
                    f"\n\n--------------\n\n"
                    f"An application has been filed for your employment as a student assistant.\n\n"
                    f"Please use the following link to review and accept the petition: {petition_url}"
                )

            else:
                # Send email asking student to upload documents
                self.email_handler.send_email(
                    recipient=petition.student_mail,
                    subject="[ClockWork] Dokumente hochladen / Upload Documents Required",
                    body=f"Für Sie wurde ein Antrag zur Einstellung als studentische Hilfskraft gestellt. Laden Sie dazu die notwendigen Unterlagen hoch. Benötigt werden\n\n"
                    f"- Selbstauskunft zur Lohnsteuererklärung (ELStAM)\n\n"
                    f"- Fragebogen zur Sozialversicherung\n\n"
                    f"- aktuelle Studienbescheinigung\n\n"
                    f"- Mitgliedsbescheinigung Ihrer Krankenkasse\n\n"
                    f"\n\n--------------\n\n"
                    f"An application has been filed for your employment as a student assistant. Please upload the required documents to complete your petition. You will need to uploade\n\n"
                    f"- Self-disclosure form for income tax (ELStAM form)\n\n"
                    f"- Social Security questionnaire\n\n"
                    f"- current certificate of enrolment\n\n"
                    f"- Health insurance membership certificate\n\n"
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
                    subject="[ClockWork] Änderung durch Kostenstellenbeauftragten angefordert / Revision requested by budget approver",
                    body=f"Für den Antrag {petition.id} auf Einstellung einer studentischen Hilfskraft wurde von einer kostenstellenverantwortlichen Person eine Änderung angefordert. "
                         f"Bitte melden Sie sich bei ClockWork an überprüfen Sie die Details des Antrags."
                         f"\n\n--------------\n\n"
                         f"An revision has been requested for the application {petition.id} for the employment of a new student assistant by another budget approver."
                         f"Please log in to ClockWork and review the application details."
                )

            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Send email to all other budget approvers
            for budget_position in budget_positions:
                if budget_position.id != requesting_budget_position.id:
                    self.email_handler.send_email(
                        recipient=budget_position.budget_approver,
                        subject="[ClockWork] Änderung durch andere Kostenstellenbeauftragten angefordert / Revision requested by another budget approver",
                        body=f"Für den Antrag {petition.id} auf Einstellung einer studentischen Hilfskraft wurde von einer anderen kostenstellenverantwortlichen Person eine Änderung angefordert. Der Antrag verzögert sich." 
                        f"\n\n--------------\n\n"
                        f"An revision has been requested for the application {petition.id} for the employment of a new student assistant by another budget approver. The application will be delayed."
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
                    subject="[ClockWork] Antrag abgelehnt / Application rejected",
                    body=f"Ihr Antrag {petition.id} auf Einstellung einer studentischen Hilfskraft wurde abgelehnt, da die Kostenstelle {rejected_budget_position.budget_position} von {rejected_budget_position.budget_approver} nicht freigegeben wurde." 
                    f"\n\n--------------\n\n" 
                    f"Your application {petition.id} for the employment of a new student assistant has been rejected. The budget {rejected_budget_position.budget_position} has not been approved by {rejected_budget_position.budget_approver}."
                )

            # Get all budget positions for this petition
            budget_positions = self.budget_position_manager.get_budget_positions_by_petition(petition.id)

            # Send email to all budget approvers (approved or not)
            for budget_position in budget_positions:
                if budget_position.id != rejected_budget_position.id:
                    self.email_handler.send_email(
                        recipient=budget_position.budget_approver,
                        subject="[ClockWork] Antrag abgebrochen / Application canceled by another person ", 
                        body=f"Der Antrag {petition.id} auf Einstellung einer studentischen Hilfskraft wurde abgebrochen, da eine der angegebenen Kostenstellen nicht freigegeben wurde.\n\nIhre Freigabe für {budget_position.budget_position} ist nicht mehr erforderlich." 
                        f"\n\n--------------\n\n" 
                        f"The application {petition.id} for the employment of a new student assistant has been canceled because another person did not approve one of the budget positions.\n\nYour review for budget position '{budget_position.budget_position}' is no longer required."
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

    def get_student_petitions(self, student_username: str) -> List[Petition]:
        petitions = self.manager.get_student_petitions(student_username)
        if not petitions:
            raise HTTPException(status_code=404, detail=f"No petitions found for student username {student_username}")
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
                employee = self.employee_manager.get_employee_by_username(petition.student_username)
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
                    subject="[ClockWork] Zustimmung durch Stud. Hilfskraft / Accepted by student assistant", 
                    body=f"Die studentische Hilfskraft hat der Einstellung zugestimmt. Der Antrag wird nun von PersonalServices geprüft." 
                    f"\n\n--------------\n\n" 
                    f"The new student assistant has agreed to the employment ({petition.id}). The application will now be reviewed by PersonalServices." 
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
                    subject="[ClockWork] Ablehnung durch Stud. Hilfskraft / Rejection by student assistant", 
                    body=f"Die studentische Hilfskraft hat der Einstellung (Antrag {petition.id}) nicht zugestimmt. Bitte melden Sie sich bei ClockWork an überprüfen Sie die Details des Antrags."
                    f"\n\n--------------\n\n" 
                    f"The student assistant has not agreed to the employment (application {petition.id}). Please log in to ClockWork and review the application details." 
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
                petition_url = f"{settings.FRONTEND_URL}/approver?petition_id={petition.id}&signature={signature}&budget_position_id={budget_position.id}"

                self.email_handler.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Antrag aktualisiert: Aktion erforderlich / Application updated: action required", 
                    body=f"Der Antrag {petition.id} wurde aktualisiert. Die Kostenstelle {budget_position.budget_position} muss erneut genehmigt werden. Bitte verwenden Sie den folgenden Link, um den Antrag zu prüfen: {petition_url}" 
                    f"\n\n--------------\n\n" 
                    f"Please review and approve the updated petition: {petition_url}"
                )

            print(f"Budget position update emails sent for petition {petition.id}", flush=True)

        except Exception as e:
            print(f"Error sending budget position update emails: {str(e)}", flush=True)

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
            employee = self.employee_manager.get_employee_by_username(petition.student_username)
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
            has_uploaded_documents = self.student_document_manager.check_student_documents_uploaded(petition.student_username)
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
                    subject="[ClockWork] Zustimmung durch Stud. Hilfskraft / Accepted by student assistant", 
                    body=f"Die neue studentische Hilfskraft hat der Einstellung zugestimmt. Der Antrag {petition.id} wird nun von PersonalServices geprüft." 
                    f"\n\n--------------\n\n"
                    f"The new student assistant has agreed to the employment. The application {petition.id} will now be reviewed by PersonalServices."
                )
        else:
            # Student rejected, notify and then move to clerk_action
            petition = self.manager.update_petition_status(petition_id, "rejected")
            if petition.supervisor_mail:
                self.email_handler.send_email(
                    recipient=petition.supervisor_mail,
                    subject="[ClockWork] Ablehnung durch Stud. Hilfskraft / Rejection by student assistant", 
                    body=f"Die studentische Hilfskraft hat der Einstellung (Antrag {petition.id}) nicht zugestimmt. Bitte melden Sie sich bei ClockWork an überprüfen Sie die Details des Antrags." 
                    f"\n\n--------------\n\n" 
                    f"The student assistant has not agreed to the employment (application {petition.id}). Please log in to ClockWork and review the application details."
                )
            for budget_position in petition.budget_positions:
                self.email_handler.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Ablehnung durch Stud. Hilfskraft / Rejection by student assistant",
                    body=f"Die studentische Hilfskraft hat der Einstellung (Antrag {petition.id}) nicht zugestimmt." 
                    f"\n\n--------------\n\n"
                    f"The student assistant has not agreed to the employment (application {petition.id})."
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
                subject="[ClockWork] Neuer Antragstatus / Application status updatee", 
                body=f"Der Antrag {petition.id} wurde von PersonalServices {'freigegeben' if approved else 'zurückgewiesen'}.\n\n" 
                f"Bitte melden Sie sich an, um den Antragsstatus zu überprüfen."
                f"\n\n--------------\n\n"
                f"Your application {petition.id} has been {'approved' if approved else 'rejected'} by PersonalServices.\n\n"
                f"Please log in and review the application's status."
            )
        for budget_position in petition.budget_positions:
            self.email_handler.send_email(
                recipient=budget_position.budget_approver,
                subject="[ClockWork] Neuer Antragstatus / Application status updatee", 
                body=f"Der Antrag {petition.id} wurde von PersonalServices {'freigegeben' if approved else 'zurückgewiesen'}." 
                f"\n\n--------------\n\n" 
                f"The application {petition.id} has been {'approved' if approved else 'rejected'} by PersonalServices."
            )
        
        if approved:
            # Create contract PDF and email it to the employee (and student)
            try:
                employee = self.employee_manager.get_employee_by_username(petition.student_username)
                if employee:
                    employee_read = EmployeeRead.model_validate(employee,from_attributes=True)
                    petition_read = PetitionRead.model_validate(petition, from_attributes=True)

                    # Create PDF bytes
                    pdf_buf = create_contract_pdf(employee_read, petition_read)
                    pdf_bytes = pdf_buf.getvalue()
                    filename = f"Arbeitsvertrag_{employee.last_name}_{employee.first_name}_{date.today().strftime('%d-%m-%Y')}.pdf"

                    # Send to employee
                    if employee.username:
                        self.email_handler.send_email(
                            recipient=employee.user_email,
                            subject="[ClockWork] Ihr Arbeitsvertrag / Your employment contract",
                            body=f"Sehr geehrte*r {employee.first_name} {employee.last_name},\n\n" 
                            f"Im Anhang finden Sie Ihren Arbeitsvertrag für Ihre Einstellung als studentische Hilfskraft (Antrag {petition.id}).\n\n"
                            f"Bitte drucken Sie diesen doppelt aus und geben Sie beide Anträge so schnell wie möglich unterschrieben an Ihren Fachbereich / Ihr Institut zurück." 
                            f"\n\n--------------\n\n" 
                            f"Dear {employee.first_name} {employee.last_name},\n\n" 
                            f"Please find attached your employment contract for your employment as student assistant (application ID {petition.id}).\n\n"
                            f"Please print it out twice and hand over the signed version to your department / institute as soon as possible.",
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
            subject="[ClockWork] Änderungen angefordert / Changes requested",
            body=f"PersonalServices hat eine Anpassung Ihrer Angaben / Unterlagen angefordert:\n\n"
            f"{message}\n\n"
            f"Bitte melden Sie sich an, um Ihre Angaben zu prüfen und zu ergänzen."
            f"\n\n--------------\n\n"
            f"PersonalServices has requested a revision of your data / documents:\n\n"
            f"{message}\n\n"
            f"Please log in to review and amend your personal information or documents."         
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
            subject="[ClockWork] Einstellung abgeschlossen / Employment process completed",
            body=f"Ihre Einstellung (Antrag {petition.id}) ist abgeschlossen.\n\n"
            f"Willkommen als Beschäftigte*r der Goethe-Universität!" 
            f"\n\n--------------\n\n" 
            f"Your employment (application ID {petition.id}) has been completed.\n\n" 
            f" Welcome as employee of Goethe University!" 
        )
        self.email_handler.send_email(
            recipient=petition.supervisor_mail,
            subject="[ClockWork] Einstellung abgeschlossen / Employment process completed",
            body=f"Der Antrag {petition.id} auf Einstellung einer studentischen Hilfskraft ist abgeschlossen.\n\n" 
            f"Sie erhalten demnächst den unterschriebenen Arbeitsvertrag von PersonalServices. Bitte geben Sie diesen an die studentische Hilfskraft weiter." 
            f"\n\n--------------\n\n" 
            f"Application {petition.id} for the employment of a student assistant has been completed.\n\n" 
            f"In a few days, you will be receiving the employment contract from PersonalServices. Please hand it over to the student assistant."
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
                    subject=f"[ClockWork] Anpassung von studentischer Hilfskraft angefordert / Review requested by student assistant",
                    body=f"Die studentische Hilfskraft ({petition.student_mail}) hat eine Anpassung des Antrags {petition.id} auf Einstellung angefordert:\n\n"
                    f"{text}\n\n"
                    f"Bitte melden Sie sich an und nehmen Sie die notwendigen Anpassungen vor."
                    f"\n\n--------------\n\n"
                    f"The student assistant({petition.student_mail}) has requested a revision for application {petition_id}:\n\n"
                    f"{text}\n\n"
                    f"Please log in and provide the necessery changes."
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