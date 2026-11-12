import logging
import smtplib
from contextlib import contextmanager
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from api.env import settings

from api.db.schema.budget_position import BudgetPosition
from api.db.schema.petition import Petition
from api.handlers.mails.mail_templates import *

logger = logging.getLogger(__name__)


class EmailHandler:
    def __init__(self, petition: Petition):
        self.petition = petition
        self.server = None

    def _render_body(self, body_de: str, body_en: str, **kwargs) -> str:
        """
        Assemble a bilingual mail body (German part, footer, separator, English part, footer)
        and fill its placeholders. The base context is available to every template;
        mail specific values are passed as kwargs and must not shadow it.
        """
        base = {
            "petition_id": self.petition.id,
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
        Only the notify_* process-step methods shall use this context manager, such that
        sending all mails of a step looks like this:

        def notify_petition_deleted(self, ...):
            with self.smtp_session():
                self._mail_petition_deleted_supervisor(...)
                self._mail_petition_deleted_student(...)
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

    def notify_student_accepted(self) -> None:
        """
        Process step: the student accepted the petition, which now moves on to PersonalServices.
        Informs the supervisor.
        """
        with self.smtp_session():
            self._mail_student_accepted_supervisor()

    def _mail_student_accepted_supervisor(self) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=STUDENT_ACCEPTED_SUPERVISOR_SUBJECT,
            body=self._render_body(STUDENT_ACCEPTED_SUPERVISOR_BODY_DE, STUDENT_ACCEPTED_SUPERVISOR_BODY_EN),
        )

    def notify_student_rejected(self, budget_positions: list[BudgetPosition]) -> None:
        """
        Process step: the student rejected the petition, which is then deleted.
        Informs the supervisor and all budget approvers.
        """
        with self.smtp_session():
            self._mail_student_rejected_supervisor()
            for budget_position in budget_positions:
                self._mail_student_rejected_approver(budget_position)

    def _mail_student_rejected_supervisor(self) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=STUDENT_REJECTED_SUBJECT,
            body=self._render_body(STUDENT_REJECTED_SUPERVISOR_BODY_DE, STUDENT_REJECTED_SUPERVISOR_BODY_EN),
        )
    # TODO: For usability purpose the budget approvers should get the information how much budget they allocated here that is freed by the rejection
    def _mail_student_rejected_approver(self, budget_position: BudgetPosition) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=STUDENT_REJECTED_SUBJECT,
            body=self._render_body(STUDENT_REJECTED_APPROVER_BODY_DE, STUDENT_REJECTED_APPROVER_BODY_EN),
        )

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

    def notify_clerk_approved(self, contract_pdf_buffer, budget_positions: list[BudgetPosition]) -> None:
        """
        Process step: PersonalServices (clerk) approved the petition.
        Sends the student the employment contract PDF and informs the supervisor and all budget approvers.
        """
        with self.smtp_session():
            self._mail_contract_student(contract_pdf_buffer)
            self._mail_clerk_approved_supervisor()
            for budget_position in budget_positions:
                self._mail_clerk_approved_approver(budget_position)

    def _mail_contract_student(self, contract_pdf_buffer) -> None:
        self.send_email(
            recipient=self.petition.student_mail,
            subject=CONTRACT_STUDENT_SUBJECT,
            body=self._render_body(CONTRACT_STUDENT_BODY_DE, CONTRACT_STUDENT_BODY_EN),
            attachment_bytes=contract_pdf_buffer.getvalue(),
            attachment_filename=f"contract_{self.petition.id}.pdf",
        )

    def _mail_clerk_approved_supervisor(self) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=CLERK_APPROVED_SUBJECT,
            body=self._render_body(CLERK_APPROVED_SUPERVISOR_BODY_DE, CLERK_APPROVED_SUPERVISOR_BODY_EN),
        )

    def _mail_clerk_approved_approver(self, budget_position: BudgetPosition) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=CLERK_APPROVED_SUBJECT,
            body=self._render_body(CLERK_APPROVED_APPROVER_BODY_DE, CLERK_APPROVED_APPROVER_BODY_EN),
        )

    def notify_clerk_requested_revision(self, message: str, subject: Optional[str] = None) -> None:
        """
        Process step: PersonalServices (clerk) requested a revision of the student's data / documents.
        Informs the student.
        """
        subject = subject or REVISION_REQUESTED_SUBJECT
        with self.smtp_session():
            self._mail_clerk_revision_student(message, subject)

    def _mail_clerk_revision_student(self, message: str, subject: str) -> None:
        self.send_email(
            recipient=self.petition.student_mail,
            subject=subject,
            body=self._render_body(
                CLERK_REVISION_STUDENT_BODY_DE,
                CLERK_REVISION_STUDENT_BODY_EN,
                message=message,
            ),
        )

    def notify_petition_completed(self) -> None:
        """
        Process step: PersonalServices (clerk) completed the employment process.
        Informs the student and the supervisor.
        """
        with self.smtp_session():
            self._mail_petition_completed_student()
            self._mail_petition_completed_supervisor()

    def _mail_petition_completed_student(self) -> None:
        self.send_email(
            recipient=self.petition.student_mail,
            subject=PETITION_COMPLETED_SUBJECT,
            body=self._render_body(PETITION_COMPLETED_STUDENT_BODY_DE, PETITION_COMPLETED_STUDENT_BODY_EN),
        )

    def _mail_petition_completed_supervisor(self) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=PETITION_COMPLETED_SUBJECT,
            body=self._render_body(PETITION_COMPLETED_SUPERVISOR_BODY_DE, PETITION_COMPLETED_SUPERVISOR_BODY_EN),
        )

    def notify_student_requested_revision(self, message: str, subject: Optional[str] = None) -> None:
        """
        Process step: the student requested a revision of the petition from the supervisor.
        Informs the supervisor, who has to make the changes.
        """
        subject = subject or REVISION_REQUESTED_SUBJECT
        with self.smtp_session():
            self._mail_student_revision_supervisor(message, subject)

    def _mail_student_revision_supervisor(self, message: str, subject: str) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=subject,
            body=self._render_body(
                STUDENT_REVISION_SUPERVISOR_BODY_DE,
                STUDENT_REVISION_SUPERVISOR_BODY_EN,
                message=message,
            ),
        )

    def notify_petition_deleted(self, reason: str, budget_positions: list[BudgetPosition]) -> None:
        """
        Process step: PersonalServices (clerk) deleted the petition, optionally giving a reason.
        Informs the supervisor, the student and all budget approvers.
        """
        reason_texts = {
            "reason_text": DELETION_REASON_DE.format(reason=reason) if reason else "",
            "reason_text_en": DELETION_REASON_EN.format(reason=reason) if reason else "",
        }
        with self.smtp_session():
            self._mail_petition_deleted_supervisor(reason_texts)
            self._mail_petition_deleted_student(reason_texts)
            for budget_position in budget_positions:
                self._mail_petition_deleted_approver(budget_position, reason_texts)

    def _mail_petition_deleted_supervisor(self, reason_texts: dict[str, str]) -> None:
        self.send_email(
            recipient=self.petition.supervisor_mail,
            subject=PETITION_DELETED_SUBJECT,
            body=self._render_body(
                PETITION_DELETED_SUPERVISOR_BODY_DE, PETITION_DELETED_SUPERVISOR_BODY_EN, **reason_texts
            ),
        )

    def _mail_petition_deleted_student(self, reason_texts: dict[str, str]) -> None:
        self.send_email(
            recipient=self.petition.student_mail,
            subject=PETITION_DELETED_SUBJECT,
            body=self._render_body(PETITION_DELETED_STUDENT_BODY_DE, PETITION_DELETED_STUDENT_BODY_EN, **reason_texts),
        )

    def _mail_petition_deleted_approver(self, budget_position: BudgetPosition, reason_texts: dict[str, str]) -> None:
        self.send_email(
            recipient=budget_position.budget_approver,
            subject=PETITION_DELETED_SUBJECT,
            body=self._render_body(
                PETITION_DELETED_APPROVER_BODY_DE, PETITION_DELETED_APPROVER_BODY_EN, **reason_texts
            ),
        )
