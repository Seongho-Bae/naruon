import socket
from unittest.mock import AsyncMock, patch

import pytest

from services import email_client
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
            smtp_username="testuser",
        )


@pytest.mark.asyncio
async def test_send_email_revalidates_smtp_host_resolution_before_connecting(
    monkeypatch,
):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "smtp.rebind.example.com"
        assert port == 587
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("10.0.0.5", port),
            )
        ]

    monkeypatch.setattr(
        "services.mail_server_security.socket.getaddrinfo", fake_getaddrinfo
    )

    with patch(
        "services.email_client.aiosmtplib.send", new_callable=AsyncMock
    ) as smtp_send:
        with pytest.raises(Exception, match="내부 네트워크"):
            await send_email(
                to_address="test@example.com",
                subject="Test Failure",
                body="Should fail before SMTP connection",
                smtp_server="smtp.rebind.example.com",
                smtp_port=587,
                smtp_username="testuser",
            )

    smtp_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_email_uses_validated_smtp_connect_ip(monkeypatch):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "smtp.public.example.com"
        assert port == 587
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.216.34", port),
            )
        ]

    calls = []

    async def fake_send(message, target, username, password):
        calls.append(
            (target.host, target.connect_host, target.port, username, password)
        )

    monkeypatch.setattr(
        "services.mail_server_security.socket.getaddrinfo", fake_getaddrinfo
    )
    monkeypatch.setattr(
        email_client, "_send_message_via_validated_smtp", fake_send, raising=False
    )

    with patch(
        "services.email_client.aiosmtplib.send", new_callable=AsyncMock
    ) as smtp_send:
        result = await email_client.send_email(
            to_address="test@example.com",
            subject="Pinned IP",
            body="Should connect to the validated IP only",
            smtp_server="smtp.public.example.com",
            smtp_port=587,
            smtp_username="testuser",
            smtp_password="secret",
        )

    assert result == {"status": "sent", "simulated": False}
    assert calls == [
        ("smtp.public.example.com", "93.184.216.34", 587, "testuser", "secret")
    ]
    smtp_send.assert_not_awaited()
