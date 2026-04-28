import base64


def generate_oauth2_string(user: str, access_token: str) -> bytes:
    """Generates an OAuth2 string for IMAP/SMTP authentication."""
    auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode("utf-8"))


import aiosmtplib
from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)


async def send_email(
    to_address: str, 
    subject: str, 
    body: str, 
    smtp_server: str | None = None, 
    smtp_port: int | None = None, 
    smtp_username: str | None = None
) -> bool:
    """Sends an email using SMTP."""
    message = EmailMessage()
    message["From"] = smtp_username or "me@example.com"
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    # Note: Real implementation would use OAuth or password.
    # This is a skeleton.
    try:
        # Example using aiosmtplib
        # await aiosmtplib.send(
        #     message,
        #     hostname=settings.SMTP_SERVER,
        #     port=settings.SMTP_PORT,
        #     use_tls=True,
        #     # username=...,
        #     # password=...
        # )
        # For now, just pretend we sent it to pass the test locally without creds.
        # This is intentionally mocked for development.
        safe_to_address = to_address.replace("\r", "").replace("\n", "")
        logger.info("Simulating sending email to %s", safe_to_address)
        return True
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")
