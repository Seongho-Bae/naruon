import base64
import logging
from email.message import EmailMessage
from typing import TypedDict
import aiosmtplib

logger = logging.getLogger(__name__)


def generate_oauth2_string(user: str, access_token: str) -> bytes:
    """Generates an OAuth2 string for IMAP/SMTP authentication."""
    auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode("utf-8"))


def _sanitize_log_value(value: str) -> str:
    """Remove CR/LF characters from user-provided values before logging."""
    return value.replace("\r", " ").replace("\n", " ")


class SendEmailResult(TypedDict):
    status: str
    simulated: bool


def build_email_message(
    to_address: str,
    subject: str,
    body: str,
    from_address: str,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> EmailMessage:
    """Build an outbound email message with optional threading headers."""
    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
    if references:
        message["References"] = references
    message.set_content(body)
    return message


async def send_email(
    to_address: str,
    subject: str,
    body: str,
    smtp_server: str | None = None,
    smtp_port: int | None = None,
    smtp_username: str | None = None,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> SendEmailResult:
    """Sends an email using SMTP."""
    safe_to_address = _sanitize_log_value(to_address)
    message = build_email_message(
        to_address=to_address,
        subject=subject,
        body=body,
        from_address=smtp_username or "me@example.com",
        in_reply_to=in_reply_to,
        references=references,
    )

    if not smtp_server or not smtp_port:
        logger.info("Simulating sending email to %s (no SMTP server configured)", safe_to_address)
        return {"status": "simulated", "simulated": True}

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_server,
            port=smtp_port,
            use_tls=True,
            # In a real system, we'd use OAuth2 or password auth here.
            # Currently we just attempt connection. If it fails, aiosmtplib raises an exception.
        )
        logger.info("Successfully sent email to %s via %s", safe_to_address, smtp_server)
        return {"status": "sent", "simulated": False}
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")
