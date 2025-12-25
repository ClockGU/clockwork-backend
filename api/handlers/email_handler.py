from api.env import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from api.db.schema.petition import Petition
    from api.db.schema.budget_position import BudgetPosition


class EmailHandler:
    def __init__(self, petition: Optional["Petition"] = None):
        self.environment = settings.APP_ENV
        self.petition = petition

    def send_email(self, recipient, subject, body, attachment_bytes: bytes = None, attachment_filename: str = None):
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        smtp_tls = settings.SMTP_TLS

        # If there is an attachment, create a multipart message
        if attachment_bytes and attachment_filename:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body))
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
            msg.attach(part)
        else:
            msg = MIMEText(body)

        msg['Subject'] = subject
        msg['From'] = smtp_user if smtp_user else "test@example.com"  # Use a dummy sender if no user is provided
        msg['To'] = recipient

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_tls:  # Only start TLS if SMTP_TLS is true
                    server.starttls()
                if smtp_user and smtp_password:  # Only login if credentials are provided
                    server.login(smtp_user, smtp_password)
                server.sendmail(msg['From'], recipient, msg.as_string())
                print(f"Email sent to {recipient}", flush=True)
        except Exception as e:
            print(f"Failed to send email: {e}", flush=True)

    def send_approval_emails(self, budget_positions: list, has_uploaded_documents: bool, is_semester_eligible: bool) -> None:
        """Send emails when all budget positions are approved"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            # Send email to supervisor
            if self.petition.supervisor_mail:
                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Kostenstellen freigegeben / Budget approved",
                    body=f"Ihr Antrag {self.petition.id} für die Einstellung einer studentischen Hilfskraft wurde von allen Kostenstellenverantwortlichen freigegeben."
                         f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n \n"
                    f"\n\n--------------\n\n"
                    f"Your application {self.petition.id} for the employment of a new student assistant has been approved by all budget approvers."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n \n"
                )

            # Send email to all budget approvers notifying them that petition is fully approved
            for budget_position in budget_positions:
                self.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Kostenstellen freigegeben / Budget approved",
                    body=f"Der Antrag {self.petition.id} für die Einstellung einer studentischen Hilfskraft wurde von allen Kostenstellenverantwortlichen freigegeben."
                         f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n \n"
                    f"\n\n--------------\n\n"
                    f"The application {self.petition.id} for the employment of a new student assistant has been approved by all budget approvers."
                         f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n \n"
                )

            if has_uploaded_documents and is_semester_eligible:
                # Generate signature for the petition acceptance link
                from api.security import generate_signature
                signature = generate_signature()
                petition_url = f"{settings.FRONTEND_URL}/student/accept?petition_id={self.petition.id}&signature={signature}"
                
                # Send email to student with acceptance link
                self.send_email(
                    recipient=self.petition.student_mail,
                    subject="[ClockWork] Antrag freigegeben / Application approved",
                    body=f"Ihr Antrag {self.petition.id} für die Einstellung als studentische Hilfskraft wurde von allen Kostenstellenverantwortlichen freigegeben.\n\n"
                    f"Bitte bestätigen Sie den Antrag unter folgendem Link:\n{petition_url}\n\n"
                    f"Sie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"Your application {self.petition.id} for employment as a student assistant has been approved by all budget approvers.\n\n"
                    f"Please confirm your application at the following link:\n{petition_url}\n\n"
                    f"You are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )
                
        except Exception as e:
            print(f"Error sending approval emails: {str(e)}", flush=True)

    def send_revision_request_email(self, requesting_budget_position: "BudgetPosition", budget_positions: list, message: Optional[str] = None) -> None:
        """Send email when a budget approver requests revision"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            revision_message = message if message else "No specific message provided."

            # Send email to supervisor
            if self.petition.supervisor_mail:
                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Änderungen angefordert / Changes requested",
                    body=f"Der Kostenstellenverantwortliche {requesting_budget_position.budget_approver} hat eine Änderung an Ihrem Antrag {self.petition.id} angefordert:\n\n"
                    f"{revision_message}\n\n"
                    f"Bitte melden Sie sich an, um die Änderungen vorzunehmen."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"The budget approver {requesting_budget_position.budget_approver} has requested changes to your application {self.petition.id}:\n\n"
                    f"{revision_message}\n\n"
                    f"Please log in to make the requested changes."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )

            # Send email to all other budget approvers
            for budget_position in budget_positions:
                if budget_position.budget_approver != requesting_budget_position.budget_approver:
                    self.send_email(
                        recipient=budget_position.budget_approver,
                        subject="[ClockWork] Änderungen angefordert / Changes requested",
                        body=f"Der Kostenstellenverantwortliche {requesting_budget_position.budget_approver} hat eine Änderung an dem Antrag {self.petition.id} angefordert:\n\n"
                        f"{revision_message}\n\n"
                        f"Sie werden benachrichtigt, sobald die Änderungen vorgenommen wurden."
                        f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"The budget approver {requesting_budget_position.budget_approver} has requested changes to application {self.petition.id}:\n\n"
                        f"{revision_message}\n\n"
                        f"You will be notified once the changes have been made."
                        f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                    )

        except Exception as e:
            print(f"Error sending revision request email: {str(e)}", flush=True)

    def send_rejection_email(self, rejected_budget_position: "BudgetPosition", budget_positions: list) -> None:
        """Send email when a budget position is rejected"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            # Send email to supervisor
            if self.petition.supervisor_mail:
                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Antrag abgelehnt / Application rejected",
                    body=f"Ihr Antrag {self.petition.id} wurde von dem Kostenstellenverantwortlichen {rejected_budget_position.budget_approver} abgelehnt."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"Your application {self.petition.id} has been rejected by the budget approver {rejected_budget_position.budget_approver}."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )

            # Send email to all budget approvers (approved or not)
            for budget_position in budget_positions:
                self.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Antrag abgelehnt / Application rejected",
                    body=f"Der Antrag {self.petition.id} wurde von dem Kostenstellenverantwortlichen {rejected_budget_position.budget_approver} abgelehnt."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"The application {self.petition.id} has been rejected by the budget approver {rejected_budget_position.budget_approver}."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )

        except Exception as e:
            print(f"Error sending rejection email: {str(e)}", flush=True)

    def send_student_acceptance_email(self) -> None:
        """Send email when student accepts the petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            # Send email to supervisor
            if self.petition.supervisor_mail:
                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Student hat zugestimmt / Student accepted",
                    body=f"Die studentische Hilfskraft hat dem Antrag {self.petition.id} zugestimmt.\n\n"
                    f"Der Antrag wird nun von PersonalServices bearbeitet."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"The student assistant has accepted application {self.petition.id}.\n\n"
                    f"The application will now be processed by PersonalServices."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )
        except Exception as e:
            print(f"Error sending student acceptance email: {str(e)}", flush=True)

    def send_student_rejection_email(self) -> None:
        """Send email when student rejects the petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            # Send email to supervisor
            if self.petition.supervisor_mail:
                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Student hat abgelehnt / Student rejected",
                    body=f"Die studentische Hilfskraft hat den Antrag {self.petition.id} abgelehnt.\n\n"
                    f"Bitte setzen Sie sich mit der studentischen Hilfskraft in Verbindung."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"The student assistant has rejected application {self.petition.id}.\n\n"
                    f"Please contact the student assistant."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )
        except Exception as e:
            print(f"Error sending student rejection email: {str(e)}", flush=True)

    def send_budget_position_update_emails(self, budget_positions: list) -> None:
        """Send emails to budget approvers when budget positions are updated"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            # due to circular import this is imported here
            from api.security import generate_signature
            signature = generate_signature()

            # Send email to all budget approvers with updated budget positions
            for budget_position in budget_positions:
                approval_url = f"{settings.FRONTEND_URL}/approver?petition_id={self.petition.id}&signature={signature}&budget_position_id={budget_position.id}"                self.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Antrag aktualisiert / Application updated",
                    body=f"Der Antrag {self.petition.id} wurde aktualisiert.\n\n"
                    f"Bitte überprüfen Sie die Änderungen und geben Sie Ihre Freigabe unter folgendem Link:\n{approval_url}\n\n"
                    f"Sie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"Application {self.petition.id} has been updated.\n\n"
                    f"Please review the changes and provide your approval at the following link:\n{approval_url}\n\n"
                    f"You are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )

            print(f"Budget position update emails sent for petition {self.petition.id}", flush=True)

        except Exception as e:
            print(f"Error sending budget position update emails: {str(e)}", flush=True)

    def send_clerk_approval_email(self, approved: bool, budget_positions: list) -> None:
        """Send email when clerk approves or rejects petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            if self.petition.supervisor_mail:
                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Neuer Antragstatus / Application status update",
                    body=f"Der Antrag {self.petition.id} wurde von PersonalServices {'freigegeben' if approved else 'zurückgewiesen'}.\n\n"
                    f"Bitte melden Sie sich an, um den Antragsstatus zu überprüfen."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"Your application {self.petition.id} has been {'approved' if approved else 'rejected'} by PersonalServices.\n\n"
                    f"Please log in and review the application's status."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )
            
            for budget_position in budget_positions:
                self.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Neuer Antragstatus / Application status update",
                    body=f"Der Antrag {self.petition.id} wurde von PersonalServices {'freigegeben' if approved else 'zurückgewiesen'}."
                         f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"The application {self.petition.id} has been {'approved' if approved else 'rejected'} by PersonalServices."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )
        except Exception as e:
            print(f"Error sending clerk approval email: {str(e)}", flush=True)

    def send_contract_pdf_email(self, contract_pdf_buffer, employee_email: str) -> None:
        """Send contract PDF to employee and student"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            # Send to employee/supervisor
            self.send_email(
                recipient=employee_email,
                subject="[ClockWork] Arbeitsvertrag / Employment contract",
                body=f"Anbei finden Sie den Arbeitsvertrag für den Antrag {self.petition.id}.\n\n"
                f"Bitte drucken Sie den Vertrag aus, unterschreiben Sie ihn und reichen Sie ihn bei PersonalServices ein."
                f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                f"\n\n--------------\n\n"
                f"Please find attached the employment contract for application {self.petition.id}.\n\n"
                f"Please print the contract, sign it and submit it to PersonalServices."
                f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                attachment_bytes=contract_pdf_buffer.getvalue(),
                attachment_filename=f"contract_{self.petition.id}.pdf"
            )

            # Send to student
            self.send_email(
                recipient=self.petition.student_mail,
                subject="[ClockWork] Arbeitsvertrag / Employment contract",
                body=f"Anbei finden Sie Ihren Arbeitsvertrag für den Antrag {self.petition.id}.\n\n"
                f"Bitte drucken Sie den Vertrag aus, unterschreiben Sie ihn und reichen Sie ihn bei PersonalServices ein."
                f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                f"\n\n--------------\n\n"
                f"Please find attached your employment contract for application {self.petition.id}.\n\n"
                f"Please print the contract, sign it and submit it to PersonalServices."
                f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                attachment_bytes=contract_pdf_buffer.getvalue(),
                attachment_filename=f"contract_{self.petition.id}.pdf"
            )

            print(f"Contract PDF sent for petition {self.petition.id}", flush=True)

        except Exception as e:
            print(f"Error sending contract PDF: {str(e)}", flush=True)

    def send_clerk_revision_request_email(self, message: str) -> None:
        """Send email when clerk requests revision from student"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            self.send_email(
                recipient=self.petition.student_mail,
                subject="[ClockWork] Änderungen angefordert / Changes requested",
                body=f"PersonalServices hat eine Anpassung Ihrer Angaben / Unterlagen angefordert:\n\n"
                f"{message}\n\n"
                f"Bitte melden Sie sich an, um Ihre Angaben zu prüfen und zu ergänzen."
                f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                f"\n\n--------------\n\n"
                f"PersonalServices has requested a revision of your data / documents:\n\n"
                f"{message}\n\n"
                f"Please log in to review and amend your personal information or documents."
                f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
            )
        except Exception as e:
            print(f"Error sending clerk revision request email: {str(e)}", flush=True)

    def send_petition_completion_emails(self) -> None:
        """Send emails when petition is completed by clerk"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            # Send email to student
            self.send_email(
                recipient=self.petition.student_mail,
                subject="[ClockWork] Einstellung abgeschlossen / Employment process completed",
                body=f"Ihre Einstellung (Antrag {self.petition.id}) ist abgeschlossen.\n\n"
                f"Willkommen als Beschäftigte*r der Goethe-Universität!"
                f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                f"\n\n--------------\n\n"
                f"Your employment (application ID {self.petition.id}) has been completed.\n\n"
                f" Welcome as employee of Goethe University!"
                f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
            )
            
            self.send_email(
                recipient=self.petition.supervisor_mail,
                subject="[ClockWork] Einstellung abgeschlossen / Employment process completed",
                body=f"Der Antrag {self.petition.id} auf Einstellung einer studentischen Hilfskraft ist abgeschlossen.\n\n"
                f"\nSie erhalten demnächst den unterschriebenen Arbeitsvertrag von PersonalServices. Bitte geben Sie diesen an die studentische Hilfskraft weiter."
                f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                f"\n\n--------------\n\n"
                f"Application {self.petition.id} for the employment of a student assistant has been completed.\n\n"
                f"In a few days, you will be receiving the employment contract from PersonalServices. Please hand it over to the student assistant."
                f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
            )
        except Exception as e:
            print(f"Error sending petition completion emails: {str(e)}", flush=True)

    def send_student_revision_request_email(self, text: str) -> None:
        """Send email when student requests revision from supervisor"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            if self.petition.supervisor_mail:
                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Änderungen angefordert / Changes requested",
                    body=f"Die studentische Hilfskraft hat eine Änderung an dem Antrag {self.petition.id} angefordert:\n\n"
                    f"{text}\n\n"
                    f"Bitte melden Sie sich an, um die Änderungen vorzunehmen."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"The student assistant has requested changes to application {self.petition.id}:\n\n"
                    f"{text}\n\n"
                    f"Please log in to make the requested changes."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )
        except Exception as e:
            print(f"Error sending student revision request email: {str(e)}", flush=True)

    def send_student_rejection_to_budget_approvers_email(self, budget_positions: list) -> None:
        """Send email to budget approvers when student rejects petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            for budget_position in budget_positions:
                self.send_email(
                    recipient=budget_position.budget_approver,
                    subject="[ClockWork] Student hat abgelehnt / Student rejected",
                    body=f"Die studentische Hilfskraft hat den Antrag {self.petition.id} abgelehnt.\n\n"
                    f"Der Antrag wird nicht weiter bearbeitet."
                    f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"The student assistant has rejected application {self.petition.id}.\n\n"
                    f"The application will not be processed further."
                    f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n"
                )
        except Exception as e:
            print(f"Error sending student rejection to budget approvers email: {str(e)}", flush=True)

    def send_student_documents_upload_request_email(self) -> None:
        """Send email asking student to upload required documents"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            self.send_email(
                recipient=self.petition.student_mail,
                subject="[ClockWork] Dokumente hochladen / Upload Documents Required",
                body=f"Für Sie wurde ein Antrag zur Einstellung als studentische Hilfskraft gestellt. Laden Sie dazu die notwendigen Unterlagen hoch. Benötigt werden\n\n"
                f"- Selbstauskunft zur Lohnsteuererklärung (ELStAM)\n\n"
                f"- Fragebogen zur Sozialversicherung\n\n"
                f"- aktuelle Studienbescheinigung\n\n"
                f"- Mitgliedsbescheinigung Ihrer Krankenkasse\n\n"
                f"\nSie bekommen diese Mail im Rahmen des Testbetriebs der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n \n"
                f"\n\n--------------\n\n"
                f"An application has been filed for your employment as a student assistant. Please upload the required documents to complete your petition. You will need to uploade\n\n"
                f"- Self-disclosure form for income tax (ELStAM form)\n\n"
                f"- Social Security questionnaire\n\n"
                f"- current certificate of enrolment\n\n"
                f"- Health insurance membership certificate\n\n"
                f"\nYou are receiving this email as part of the testing phase of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n \n"
            )
        except Exception as e:
            print(f"Error sending student documents upload request email: {str(e)}", flush=True)

    def send_student_acceptance_link_email(self, signature: str) -> None:
        """Send email to student with acceptance link"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        
        try:
            petition_url = f"{settings.FRONTEND_URL}/student/accept?petition_id={self.petition.id}&signature={signature}"
            
            self.send_email(
                recipient=self.petition.student_mail,
                subject="[ClockWork] Einstellung als studentische Hilfskraft / Employment as a student assistant",
                body=f"Für Sie wurde ein Antrag zur Einstellung als studentische Hilfskraft gestellt.\n\n"
                f"Bitte nutzen Sie den folgenden Link, um sich anzumelden und dem Antrag zuzustimmen: {petition_url}"
                f"\n\n--------------\n\n"
                f"An application has been filed for your employment as a student assistant.\n\n"
                f"Please use the following link to review and accept the petition: {petition_url}"
            )
        except Exception as e:
            print(f"Error sending student acceptance link email: {str(e)}", flush=True)