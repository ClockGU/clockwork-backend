import logging
import smtplib
from contextlib import contextmanager
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Optional

from api.env import settings

from api.db.schema.budget_position import BudgetPosition
from api.db.schema.petition import Petition
from api.handlers.mail_templates import (
    ACCEPTANCE_LINK_STUDENT_BODY_DE,
    ACCEPTANCE_LINK_STUDENT_BODY_EN,
    ACCEPTANCE_LINK_STUDENT_SUBJECT,
    APPROVAL_REQUEST_APPROVER_BODY_DE,
    APPROVAL_REQUEST_APPROVER_BODY_EN,
    APPROVAL_REQUEST_APPROVER_SUBJECT,
    APPROVER_REVISION_APPROVER_BODY_DE,
    APPROVER_REVISION_APPROVER_BODY_EN,
    APPROVER_REVISION_SUPERVISOR_BODY_DE,
    APPROVER_REVISION_SUPERVISOR_BODY_EN,
    BUDGET_APPROVED_APPROVER_BODY_DE,
    BUDGET_APPROVED_APPROVER_BODY_EN,
    BUDGET_APPROVED_SUBJECT,
    BUDGET_APPROVED_SUPERVISOR_BODY_DE,
    BUDGET_APPROVED_SUPERVISOR_BODY_EN,
    BUDGET_REJECTED_APPROVER_BODY_DE,
    BUDGET_REJECTED_APPROVER_BODY_EN,
    BUDGET_REJECTED_SUBJECT,
    BUDGET_REJECTED_SUPERVISOR_BODY_DE,
    BUDGET_REJECTED_SUPERVISOR_BODY_EN,
    FOOTER_DE,
    FOOTER_EN,
    NO_REVISION_MESSAGE,
    PETITION_CREATED_STUDENT_BODY_DE,
    PETITION_CREATED_STUDENT_BODY_EN,
    PETITION_CREATED_STUDENT_SUBJECT,
    PETITION_UPDATED_APPROVER_BODY_DE,
    PETITION_UPDATED_APPROVER_BODY_EN,
    PETITION_UPDATED_SUBJECT,
    REVISION_REQUESTED_SUBJECT,
    SEPARATOR,
    UPLOAD_REQUEST_STUDENT_BODY_DE,
    UPLOAD_REQUEST_STUDENT_BODY_EN,
    UPLOAD_REQUEST_STUDENT_SUBJECT,
)

logger = logging.getLogger(__name__)


class EmailHandler:
    def __init__(self, petition: Optional["Petition"] = None):
        self.petition = petition
        self.server = None

    def _render_body(self, body_de: str, body_en: str, **kwargs) -> str:
        """
        Assemble a bilingual mail body (German part, footer, separator, English part, footer)
        and fill its placeholders. The base context is available to every template;
        mail specific values are passed as kwargs and must not shadow it.
        """
        base = {
            "petition_id": self.petition.id if self.petition else None,
            "support_mail": settings.SMTP_USER,
            "frontend_url": settings.FRONTEND_URL,
        }
        shadowed = base.keys() & kwargs.keys()
        if shadowed:
            raise ValueError(f"Mail kwargs must not override base context: {sorted(shadowed)}")
        return (body_de + FOOTER_DE + SEPARATOR + body_en + FOOTER_EN).format(**base, **kwargs)

    def _approver_url(self, budget_position: BudgetPosition, signature: str) -> str:
        """Signed link for a budget approver to review the petition for their budget position."""
        return (
            f"{settings.FRONTEND_URL}/approver?petition_id={self.petition.id}"
            f"&signature={signature}&budget_position_id={budget_position.id}"
        )

    def get_or_create_smtp_server(self):
        if self.server is None:
            self._setup_smtp_server()
        return self.server

    def _setup_smtp_server(self):
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        smtp_tls = settings.SMTP_TLS
        server = smtplib.SMTP(smtp_server, smtp_port)
        if smtp_tls:  # Only start TLS if SMTP_TLS is true
            server.starttls()
        if smtp_user and smtp_password:  # Only login if credentials are provided
            server.login(smtp_user, smtp_password)
        self.server = server

    def _close_server(self):
        self.server.quit()
        self.server = None

    @contextmanager
    def smtp_session(self):
        """
        Context manager for all email sending operations.
        This way the send_email method does not have to setup a connection
        everytime but is able to reuse them if in the same conext.

        Example usage:
        Only wrapper methods shall use this context manager such that if sending
        mail to 3 addresses would look like this:

        def send_petition_deletion_mails(self):
            with self.smtp_session():
                self.send_email(recipient=address1, subject="...", body="...")
                self.send_email(recipient=address2, subject="...", body="...")
                ...

        """
        try:
            server = self.get_or_create_smtp_server()
        except Exception:
            logger.exception(
                "Could not connect to SMTP server %s:%s",
                settings.SMTP_SERVER,
                settings.SMTP_PORT,
            )
            raise
        try:
            yield server
        finally:
            if self.server is not None:
                self._close_server()

    def send_email(
        self,
        recipient,
        subject,
        body,
        attachment_bytes: bytes = None,
        attachment_filename: str = None,
    ):
        smtp_user = settings.SMTP_USER


        # If there is an attachment, create a multipart message
        if attachment_bytes and attachment_filename:
            msg = MIMEMultipart()
            msg.attach(MIMEText(body))
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment_bytes)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f'attachment; filename="{attachment_filename}"'
            )
            msg.attach(part)
        else:
            msg = MIMEText(body)

        msg["Subject"] = subject
        msg["From"] = (
            smtp_user if smtp_user else "test@example.com"
        )  # Use a dummy sender if no user is provided
        msg["To"] = recipient

        try:
            self.server.sendmail(msg["From"], recipient, msg.as_string())
            logger.info("Mail sent to %s: %s", recipient, subject)
        except Exception:
            logger.exception("Failed to send mail to %s: %s", recipient, subject)

    def notify_petition_created(self, budget_positions: list[BudgetPosition]) -> None:
        """
        Process step: the supervisor created a petition.
        Informs the student and sends every budget approver an approval request with a signed link.
        """
        # Local import: api.security imports api.handlers, a top-level import would be circular.
        from api.security import generate_signature

        signature = generate_signature()
        with self.smtp_session():
            self._mail_petition_created_student()
            for budget_position in budget_positions:
                self._mail_approval_request_approver(budget_position, signature)

    def _mail_petition_created_student(self) -> None:
        if not self.petition.student_mail:
            return
        self.send_email(
            recipient=self.petition.student_mail,
            subject=PETITION_CREATED_STUDENT_SUBJECT,
            body=self._render_body(PETITION_CREATED_STUDENT_BODY_DE, PETITION_CREATED_STUDENT_BODY_EN),
        )

    def _mail_approval_request_approver(self, budget_position: BudgetPosition, signature: str) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=APPROVAL_REQUEST_APPROVER_SUBJECT,
            body=self._render_body(
                APPROVAL_REQUEST_APPROVER_BODY_DE,
                APPROVAL_REQUEST_APPROVER_BODY_EN,
                budget_position=budget_position.budget_position,
                approval_url=self._approver_url(budget_position, signature),
            ),
        )

    def notify_budget_approved(
        self, budget_positions: list[BudgetPosition], has_approved_petition_in_semester: bool
    ) -> None:
        """
        Process step: all budget positions of the petition are approved.
        Informs the supervisor and all budget approvers. The student either gets the acceptance link
        (fast track: already approved petition in the same semester, so all documents are valid)
        or a request to upload the required documents.
        """
        with self.smtp_session():
            self._mail_budget_approved_supervisor()
            for budget_position in budget_positions:
                self._mail_budget_approved_approver(budget_position)
            if has_approved_petition_in_semester:
                # Local import: api.security imports api.handlers, a top-level import would be circular.
                from api.security import generate_signature

                self._mail_acceptance_link_student(generate_signature())
            else:
                self._mail_upload_request_student()

    def _mail_budget_approved_supervisor(self) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=BUDGET_APPROVED_SUBJECT,
            body=self._render_body(BUDGET_APPROVED_SUPERVISOR_BODY_DE, BUDGET_APPROVED_SUPERVISOR_BODY_EN),
        )

    def _mail_budget_approved_approver(self, budget_position: BudgetPosition) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=BUDGET_APPROVED_SUBJECT,
            body=self._render_body(BUDGET_APPROVED_APPROVER_BODY_DE, BUDGET_APPROVED_APPROVER_BODY_EN),
        )

    def _mail_acceptance_link_student(self, signature: str) -> None:
        acceptance_url = (
            f"{settings.FRONTEND_URL}/student/accept?petition_id={self.petition.id}&signature={signature}"
        )
        self.send_email(
            recipient=self.petition.student_mail,
            subject=ACCEPTANCE_LINK_STUDENT_SUBJECT,
            body=self._render_body(
                ACCEPTANCE_LINK_STUDENT_BODY_DE,
                ACCEPTANCE_LINK_STUDENT_BODY_EN,
                acceptance_url=acceptance_url,
            ),
        )

    def _mail_upload_request_student(self) -> None:
        dashboard_url = f"{settings.FRONTEND_URL}/dashboard/student"
        self.send_email(
            recipient=self.petition.student_mail,
            subject=UPLOAD_REQUEST_STUDENT_SUBJECT,
            body=self._render_body(
                UPLOAD_REQUEST_STUDENT_BODY_DE,
                UPLOAD_REQUEST_STUDENT_BODY_EN,
                dashboard_url=dashboard_url,
            ),
        )

    def notify_revision_requested_by_approver(
        self,
        requesting_budget_position: BudgetPosition,
        budget_positions: list[BudgetPosition],
        message: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> None:
        """
        Process step: a budget approver requested a revision of the petition.
        Informs the supervisor (who has to make the changes) and all other budget approvers.
        """
        message = message or NO_REVISION_MESSAGE
        subject = subject or REVISION_REQUESTED_SUBJECT
        requesting_approver = requesting_budget_position.budget_approver
        with self.smtp_session():
            self._mail_approver_revision_supervisor(requesting_approver, message, subject)
            for budget_position in budget_positions:
                if budget_position.budget_approver != requesting_approver:
                    self._mail_approver_revision_approver(budget_position, requesting_approver, message, subject)

    def _mail_approver_revision_supervisor(self, requesting_approver: str, message: str, subject: str) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=subject,
            body=self._render_body(
                APPROVER_REVISION_SUPERVISOR_BODY_DE,
                APPROVER_REVISION_SUPERVISOR_BODY_EN,
                requesting_approver=requesting_approver,
                message=message,
            ),
        )

    def _mail_approver_revision_approver(
        self, budget_position: BudgetPosition, requesting_approver: str, message: str, subject: str
    ) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=subject,
            body=self._render_body(
                APPROVER_REVISION_APPROVER_BODY_DE,
                APPROVER_REVISION_APPROVER_BODY_EN,
                requesting_approver=requesting_approver,
                message=message,
            ),
        )

    def notify_budget_rejected(
        self, rejected_budget_position: BudgetPosition, budget_positions: list[BudgetPosition]
    ) -> None:
        """
        Process step: a budget approver rejected their budget position, which rejects the petition.
        Informs the supervisor and all budget approvers (including the rejecting one).
        """
        rejecting_approver = rejected_budget_position.budget_approver
        with self.smtp_session():
            self._mail_budget_rejected_supervisor(rejecting_approver)
            for budget_position in budget_positions:
                self._mail_budget_rejected_approver(budget_position, rejecting_approver)

    def _mail_budget_rejected_supervisor(self, rejecting_approver: str) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=BUDGET_REJECTED_SUBJECT,
            body=self._render_body(
                BUDGET_REJECTED_SUPERVISOR_BODY_DE,
                BUDGET_REJECTED_SUPERVISOR_BODY_EN,
                rejecting_approver=rejecting_approver,
            ),
        )

    def _mail_budget_rejected_approver(self, budget_position: BudgetPosition, rejecting_approver: str) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=BUDGET_REJECTED_SUBJECT,
            body=self._render_body(
                BUDGET_REJECTED_APPROVER_BODY_DE,
                BUDGET_REJECTED_APPROVER_BODY_EN,
                rejecting_approver=rejecting_approver,
            ),
        )

    def send_student_acceptance_email(self) -> None:
        """Send email when student accepts the petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        with self.smtp_session():
            try:
                # Send email to supervisor
                if self.petition.supervisor_mail:
                    self.send_email(
                        recipient=self.petition.supervisor_mail,
                        subject="[ClockWork] Student hat zugestimmt / Student accepted",
                        body=f"Die studentische Hilfskraft hat dem Antrag {self.petition.id} zugestimmt.\n\n"
                        f"Der Antrag wird nun von PersonalServices bearbeitet."
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"The student assistant has accepted application {self.petition.id}.\n\n"
                        f"The application will now be processed by PersonalServices."
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )
            except Exception as e:
                print(f"Error sending student acceptance email: {str(e)}", flush=True)

    def send_student_rejection_email(self) -> None:
        """Send email when student rejects the petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")

        with self.smtp_session():
            try:
                # Send email to supervisor
                if self.petition.supervisor_mail:
                    self.send_email(
                        recipient=self.petition.supervisor_mail,
                        subject="[ClockWork] Student hat abgelehnt / Student rejected",
                        body=f"Die studentische Hilfskraft hat den Antrag {self.petition.id} abgelehnt.\n\n"
                        f"Bitte setzen Sie sich mit der studentischen Hilfskraft in Verbindung."
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"The student assistant has rejected application {self.petition.id}.\n\n"
                        f"Please contact the student assistant."
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )
            except Exception as e:
                print(f"Error sending student rejection email: {str(e)}", flush=True)

    def notify_petition_updated(self, budget_positions: list[BudgetPosition]) -> None:
        """
        Process step: the supervisor updated the petition, which resets all budget approvals.
        Sends every budget approver a new approval request with a signed link.
        """
        # Local import: api.security imports api.handlers, a top-level import would be circular.
        from api.security import generate_signature

        signature = generate_signature()
        with self.smtp_session():
            for budget_position in budget_positions:
                self._mail_petition_updated_approver(budget_position, signature)

    def _mail_petition_updated_approver(self, budget_position: BudgetPosition, signature: str) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=PETITION_UPDATED_SUBJECT,
            body=self._render_body(
                PETITION_UPDATED_APPROVER_BODY_DE,
                PETITION_UPDATED_APPROVER_BODY_EN,
                approval_url=self._approver_url(budget_position, signature),
            ),
        )

    def send_clerk_approval_email(
        self, budget_positions: list["BudgetPosition"]
    ) -> None:
        """Send email when clerk approves or rejects petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        with self.smtp_session():
            try:
                if self.petition.supervisor_mail:
                    self.send_email(
                        recipient=self.petition.supervisor_mail,
                        subject="[ClockWork] Neuer Antragstatus / Application status update",
                        body=f"Der Antrag {self.petition.id} wurde von PersonalServices freigegeben.\n\n"
                        f"Bitte melden Sie sich an, um den Antragsstatus zu überprüfen."
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"Your application {self.petition.id} has been approved by PersonalServices.\n\n"
                        f"Please log in and review the application's status."
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )

                for budget_position in budget_positions:
                    self.send_email(
                        recipient=budget_position.budget_approver,
                        subject="[ClockWork] Neuer Antragstatus / Application status update",
                        body=f"Der Antrag {self.petition.id} wurde von PersonalServices freigegeben."
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"The application {self.petition.id} has been approved by PersonalServices."
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )
            except Exception as e:
                print(f"Error sending clerk approval email: {str(e)}", flush=True)

    def send_contract_pdf_email(self, contract_pdf_buffer) -> None:
        """Send contract PDF to employee and student"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")
        with self.smtp_session():
            try:
                self.send_email(
                    recipient=self.petition.student_mail,
                    subject="[ClockWork] Arbeitsvertrag / Employment contract",
                    body=f"Anbei finden Sie Ihren Arbeitsvertrag für den Antrag {self.petition.id}.\n\n"
                    f"Bitte drucken Sie den Vertrag aus, unterschreiben Sie ihn und reichen Sie ihn bei PersonalServices ein."
                    f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"Please find attached your employment contract for application {self.petition.id}.\n\n"
                    f"Please print the contract, sign it and submit it to PersonalServices."
                    f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    attachment_bytes=contract_pdf_buffer.getvalue(),
                    attachment_filename=f"contract_{self.petition.id}.pdf",
                )

                print(f"Contract PDF sent for petition {self.petition.id}", flush=True)

            except Exception as e:
                print(f"Error sending contract PDF: {str(e)}", flush=True)

    def send_clerk_revision_request_email(
        self, message: str, subject: Optional[str] = None
    ) -> None:
        """Send email when clerk requests revision from student"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")

        with self.smtp_session():
            try:
                email_subject = (
                    subject
                    if subject
                    else "[ClockWork] Änderungen angefordert / Changes requested"
                )
                self.send_email(
                    recipient=self.petition.student_mail,
                    subject=email_subject,
                    body=f"PersonalServices hat eine Anpassung Ihrer Angaben / Unterlagen angefordert:\n\n"
                    f"{message}\n\n"
                    f"Bitte melden Sie sich an, um Ihre Angaben zu prüfen und zu ergänzen."
                    f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"PersonalServices has requested a revision of your data / documents:\n\n"
                    f"{message}\n\n"
                    f"Please log in to review and amend your personal information or documents."
                    f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                )
            except Exception as e:
                print(f"Error sending clerk revision request email: {str(e)}", flush=True)

    def send_petition_completion_emails(self) -> None:
        """Send emails when petition is completed by clerk"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")

        with self.smtp_session():
            try:
                # Send email to student
                self.send_email(
                    recipient=self.petition.student_mail,
                    subject="[ClockWork] Einstellung abgeschlossen / Employment process completed",
                    body=f"Ihre Einstellung (Antrag {self.petition.id}) ist abgeschlossen.\n\n"
                    f"Willkommen als Beschäftigte*r der Goethe-Universität!"
                    f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"Your employment (application ID {self.petition.id}) has been completed.\n\n"
                    f" Welcome as employee of Goethe University!"
                    f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                )

                self.send_email(
                    recipient=self.petition.supervisor_mail,
                    subject="[ClockWork] Einstellung abgeschlossen / Employment process completed",
                    body=f"Der Antrag {self.petition.id} auf Einstellung einer studentischen Hilfskraft ist abgeschlossen.\n\n"
                    f"\nSie erhalten demnächst den unterschriebenen Arbeitsvertrag von PersonalServices. Bitte geben Sie diesen an die studentische Hilfskraft weiter."
                    f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                    f"\n\n--------------\n\n"
                    f"Application {self.petition.id} for the employment of a student assistant has been completed.\n\n"
                    f"In a few days, you will be receiving the employment contract from PersonalServices. Please hand it over to the student assistant."
                    f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                )
            except Exception as e:
                print(f"Error sending petition completion emails: {str(e)}", flush=True)

    def send_student_revision_request_email(
        self, text: str, subject: Optional[str] = None
    ) -> None:
        """Send email when student requests revision from supervisor"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")

        with self.smtp_session():
            try:
                email_subject = (
                    subject
                    if subject
                    else "[ClockWork] Änderungen angefordert / Changes requested"
                )
                if self.petition.supervisor_mail:
                    self.send_email(
                        recipient=self.petition.supervisor_mail,
                        subject=email_subject,
                        body=f"Die studentische Hilfskraft hat eine Änderung an dem Antrag {self.petition.id} angefordert:\n\n"
                        f"{text}\n\n"
                        f"Bitte melden Sie sich an, um die Änderungen vorzunehmen."
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"The student assistant has requested changes to application {self.petition.id}:\n\n"
                        f"{text}\n\n"
                        f"Please log in to make the requested changes."
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )
            except Exception as e:
                print(f"Error sending student revision request email: {str(e)}", flush=True)

    def send_student_rejection_to_budget_approvers_email(
        self, budget_positions: list
    ) -> None:
        """Send email to budget approvers when student rejects petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")

        with self.smtp_session():
            try:
                for budget_position in budget_positions:
                    self.send_email(
                        recipient=budget_position.budget_approver,
                        subject="[ClockWork] Student hat abgelehnt / Student rejected",
                        body=f"Die studentische Hilfskraft hat den Antrag {self.petition.id} abgelehnt.\n\n"
                        f"Der Antrag wird nicht weiter bearbeitet."
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"The student assistant has rejected application {self.petition.id}.\n\n"
                        f"The application will not be processed further."
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )
            except Exception as e:
                print(
                    f"Error sending student rejection to budget approvers email: {str(e)}",
                    flush=True,
                )

    def send_clerk_deletion_email(self, reason: str, budget_positions: list) -> None:
        """Send email when clerk deletes a petition"""
        if not self.petition:
            raise ValueError("Petition is required for this email operation")

        with self.smtp_session():
            try:
                reason_text = f"\n\nBegründung:\n{reason}" if reason else ""
                reason_text_en = f"\n\nReason:\n{reason}" if reason else ""

                # Send email to supervisor
                if self.petition.supervisor_mail:
                    self.send_email(
                        recipient=self.petition.supervisor_mail,
                        subject="[ClockWork] Antrag gelöscht / Application deleted",
                        body=f"Ihr Antrag {self.petition.id} wurde von PersonalServices gelöscht.{reason_text}"
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"Your application {self.petition.id} has been deleted by PersonalServices.{reason_text_en}"
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )

                # Send email to student
                if self.petition.student_mail:
                    self.send_email(
                        recipient=self.petition.student_mail,
                        subject="[ClockWork] Antrag gelöscht / Application deleted",
                        body=f"Ihr Antrag {self.petition.id} zur Einstellung als studentische Hilfskraft wurde von PersonalServices gelöscht.{reason_text}"
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"Your application {self.petition.id} for employment as a student assistant has been deleted by PersonalServices.{reason_text_en}"
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )

                # Send email to all budget approvers
                for budget_position in budget_positions:
                    self.send_email(
                        recipient=budget_position.budget_approver,
                        subject="[ClockWork] Antrag gelöscht / Application deleted",
                        body=f"Der Antrag {self.petition.id} wurde von PersonalServices gelöscht.{reason_text}"
                        f"\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. Bei Fragen oder Problemen wenden Sie sich bitte an {settings.SMTP_USER}. \n"
                        f"\n\n--------------\n\n"
                        f"The application {self.petition.id} has been deleted by PersonalServices.{reason_text_en}"
                        f"\nYou are receiving this email as part of student employment process of the software, Clockwork. If you have any questions or encounter any problems, please email {settings.SMTP_USER}. \n",
                    )
            except Exception as e:
                print(f"Error sending clerk deletion email: {str(e)}", flush=True)
