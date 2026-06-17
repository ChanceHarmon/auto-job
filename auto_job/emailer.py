import os
import smtplib

from email.message import EmailMessage

from dotenv import load_dotenv

from auto_job.config import AppConfig

load_dotenv()


def send_report_email(
    report: str,
    config: AppConfig,
    subject: str = "Auto-job report",
) -> bool:
    """Send a plain-text job report email."""

    # Return False for configuration issues instead of raising so a daily run
    # can still save the report locally even when email is disabled or mis-set.
    if not config.email.enabled:
        print("Email is disabled in config.yaml")
        return False

    if not config.email.to or not config.email.from_email:
        print("Missing email.to or email.from_email in config.yaml")
        return False

    password = os.getenv("AUTO_JOB_EMAIL_PASSWORD")

    if not password:
        print("Missing AUTO_JOB_EMAIL_PASSWORD environment variable")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.email.from_email
    message["To"] = config.email.to
    message.set_content(report)

    # SMTP is intentionally plain and local-config driven; the app does not
    # store credentials, only reads the app password from the environment.
    with smtplib.SMTP(config.email.smtp_host, config.email.smtp_port) as smtp:
        smtp.starttls()
        smtp.login(config.email.from_email, password)
        smtp.send_message(message)

    return True
