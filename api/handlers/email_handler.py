from api.env import settings
import smtplib
from email.mime.text import MIMEText



class EmailHandler:
    def __init__(self):
        self.environment = settings.APP_ENV

    def send_email(self, recipient, subject, body):
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        smtp_tls = settings.SMTP_TLS

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