import pytest
from services.email_client import send_email

@pytest.mark.asyncio
async def test_send_email_raises_error_when_smtp_fails():
    with pytest.raises(Exception, match="Failed to send email"):
        await send_email(
            to_address="test@example.com",
            subject="Test Failure",
            body="Should fail because SMTP server is invalid",
            smtp_server="invalid.example.com",
            smtp_port=587,
            smtp_username="testuser"
        )
