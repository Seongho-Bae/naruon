import base64
import pytest
from services.email_client import build_email_message, generate_oauth2_string


def test_generate_oauth2_string():
    result = generate_oauth2_string("test@example.com", "dummy_token")
    decoded = base64.b64decode(result)
    assert b"user=test@example.com" in decoded
    assert b"auth=Bearer dummy_token" in decoded


def test_build_email_message_sets_reply_headers():
    message = build_email_message(
        to_address="test@example.com",
        subject="Re: Test",
        body="Reply body",
        from_address="sender@example.com",
        in_reply_to="<parent@example.com>",
        references="<root@example.com> <parent@example.com>",
    )

    assert message["In-Reply-To"] == "<parent@example.com>"
    assert message["References"] == "<root@example.com> <parent@example.com>"
    assert message["From"] == "sender@example.com"
    assert message["To"] == "test@example.com"
