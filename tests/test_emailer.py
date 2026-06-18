# Tests for email delivery setup without connecting to a real SMTP server.

from auto_job.config import AppConfig
from auto_job.emailer import send_report_email


def build_email_config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "search": {},
            "filters": {},
            "sources": {},
            "email": {
                "enabled": True,
                "to": "to@example.com",
                "from_email": "from@example.com",
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
            },
        }
    )


def test_send_report_email_includes_html_alternative(monkeypatch):
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def starttls(self):
            pass

        def login(self, from_email, password):
            pass

        def send_message(self, message):
            sent_messages.append(message)

    monkeypatch.setenv("AUTO_JOB_EMAIL_PASSWORD", "password")
    monkeypatch.setattr("auto_job.emailer.smtplib.SMTP", FakeSMTP)

    sent = send_report_email(
        "Plain report",
        build_email_config(),
        html_report="<p>HTML report</p>",
    )

    assert sent is True
    assert len(sent_messages) == 1
    assert sent_messages[0].is_multipart()
    assert sent_messages[0].get_body(("plain",)).get_content() == "Plain report\n"
    assert sent_messages[0].get_body(("html",)).get_content() == "<p>HTML report</p>\n"
