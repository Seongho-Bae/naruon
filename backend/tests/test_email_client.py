import base64
import logging
import pytest
from services.email_client import (
    _sanitize_log_value,
    build_email_message,
    generate_oauth2_string,
    send_email,
)


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


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        ("to_address", {"to_address": "victim@example.com\r\nBcc: spy@example.com"}),
        ("from_address", {"from_address": "sender@example.com\nBcc: spy@example.com"}),
        ("subject", {"subject": "Quarterly update\r\nBcc: spy@example.com"}),
        (
            "in_reply_to",
            {"in_reply_to": "<parent@example.com>\r\nBcc: spy@example.com"},
        ),
        ("references", {"references": "<root@example.com>\x00<parent@example.com>"}),
    ],
)
def test_build_email_message_rejects_header_control_characters(field, kwargs):
    payload = {
        "to_address": "test@example.com",
        "subject": "Re: Test",
        "body": "Reply body",
        "from_address": "sender@example.com",
        "in_reply_to": "<parent@example.com>",
        "references": "<root@example.com> <parent@example.com>",
    }
    payload.update(kwargs)

    with pytest.raises(ValueError, match=field):
        build_email_message(**payload)


@pytest.mark.asyncio
async def test_send_email_logs_sanitized_recipient(caplog):
    caplog.set_level(logging.INFO, logger="services.email_client")

    result = await send_email(
        to_address="victim@example.com",
        subject="Test",
        body="Body",
    )

    assert result == {"status": "simulated", "simulated": True}
    messages = [record.getMessage() for record in caplog.records]
    assert "Simulating sending email to victim@example.com" in messages
    assert all("\n" not in message and "\r" not in message for message in messages)


def test_log_value_sanitizer_removes_crlf():
    assert (
        _sanitize_log_value("victim@example.com\r\nINFO forged@example.com")
        == "victim@example.com  INFO forged@example.com"
    )
