from api.env import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders



class EmailHandler:
    def __init__(self):
        self.environment = settings.APP_ENV

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