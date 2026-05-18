import inspect
import socket

import pytest
import services.email_client as email_client
from services.email_client import build_email_message, send_email
from services.email_client import _build_smtp_client
from services.email_client import _send_pinned_smtp_message


def _make_socket() -> socket.socket:
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_smtp_host_policy_denies_empty_allowlist_before_dns(monkeypatch):
    monkeypatch.setattr(email_client.settings, "ALLOWED_SMTP_HOSTS", "")

    def fail_getaddrinfo(*args, **kwargs):
        raise AssertionError("empty SMTP allowlist must fail before DNS resolution")

    monkeypatch.setattr(email_client.socket, "getaddrinfo", fail_getaddrinfo)

    with pytest.raises(ValueError, match=email_client.SMTP_HOST_NOT_ALLOWED):
        email_client.validate_smtp_host("smtp.example.com", resolve_host=True)


def test_smtp_host_policy_keeps_empty_allowlist_guard_explicit():
    source = inspect.getsource(email_client.validate_smtp_host)

    assert "if not allowed_hosts or" not in source
    assert "if not allowed_hosts:" in source
    assert "if normalized_host not in allowed_hosts:" in source


def test_smtp_host_policy_rejects_wildcard_allowlist_entry(monkeypatch):
    monkeypatch.setattr(
        email_client.settings,
        "ALLOWED_SMTP_HOSTS",
        "smtp.example.com,*",
    )
    monkeypatch.setattr(
        email_client.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 587))
        ],
    )

    with pytest.raises(ValueError, match=email_client.SMTP_HOST_NOT_ALLOWED):
        email_client.validate_smtp_host("smtp.example.com", resolve_host=True)


def test_smtp_port_policy_rejects_configured_non_smtp_ports(monkeypatch):
    monkeypatch.setattr(email_client.settings, "ALLOWED_SMTP_PORTS", "465,587,80")

    with pytest.raises(ValueError, match=email_client.SMTP_PORT_NOT_ALLOWED):
        email_client.validate_smtp_port(80)


class FakeSmtpClient:
    def __init__(self, *, fail_send=False):
        self.fail_send = fail_send
        self.entered = False
        self.exited = False
        self.starttls_hostname = None
        self.login_args = None
        self.sent_message = None

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        self.exited = True

    async def starttls(self, *, server_hostname):
        self.starttls_hostname = server_hostname

    async def login(self, username, password):
        self.login_args = (username, password)

    async def send_message(self, message):
        if self.fail_send:
            raise RuntimeError("smtp unavailable")
        self.sent_message = message


@pytest.mark.asyncio
async def test_send_email_rejects_private_smtp_host_before_network(monkeypatch):
    async def fail_if_called(*args, **kwargs):
        raise AssertionError("aiosmtplib.send must not be called")

    monkeypatch.setattr("services.email_client.aiosmtplib.send", fail_if_called)

    with pytest.raises(ValueError, match="SMTP server is not allowed"):
        await send_email(
            to_address="test@example.com",
            subject="Test",
            body="Body",
            smtp_server="127.0.0.1",
            smtp_port=587,
            smtp_username="testuser",
        )


@pytest.mark.asyncio
async def test_send_email_uses_validated_address_without_second_dns(monkeypatch):
    async def fail_legacy_send(*args, **kwargs):
        raise AssertionError("aiosmtplib.send must not resolve the hostname again")

    smtp_socket = _make_socket()

    async def fake_pinned_send(message, **kwargs):
        assert kwargs["smtp_socket"] is smtp_socket
        assert kwargs["smtp_server"] == "smtp.example.com"
        assert kwargs["smtp_port"] == 587
        return {"status": "sent", "simulated": False}

    async def fake_connect_validated_socket(smtp_server, smtp_port):
        assert smtp_server == "smtp.example.com"
        assert smtp_port == 587
        return smtp_socket

    monkeypatch.setattr("services.email_client.aiosmtplib.send", fail_legacy_send)
    monkeypatch.setattr(
        "services.email_client._send_pinned_smtp_message",
        fake_pinned_send,
        raising=False,
    )
    monkeypatch.setattr(
        "services.email_client._connect_validated_smtp_socket",
        fake_connect_validated_socket,
        raising=False,
    )

    validate_calls = []

    def fake_validate_smtp_destination(smtp_server, smtp_port, *, resolve_host=True):
        validate_calls.append(resolve_host)
        return smtp_server, smtp_port

    monkeypatch.setattr(
        "services.email_client.validate_smtp_destination",
        fake_validate_smtp_destination,
    )

    result = await send_email(
        to_address="test@example.com",
        subject="Test",
        body="Body",
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_username="testuser",
    )

    assert result == {"status": "sent", "simulated": False}
    assert validate_calls == [True]
    assert smtp_socket.fileno() == -1


@pytest.mark.asyncio
async def test_pinned_smtp_send_passes_original_hostname_and_socket(monkeypatch):
    smtp_socket = _make_socket()
    fake_client = FakeSmtpClient()
    message = build_email_message(
        to_address="test@example.com",
        subject="Test",
        body="Body",
        from_address="sender@example.com",
    )

    def fake_build_client(**kwargs):
        assert kwargs == {
            "smtp_socket": smtp_socket,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
        }
        return fake_client

    monkeypatch.setattr("services.email_client._build_smtp_client", fake_build_client)

    result = await _send_pinned_smtp_message(
        message,
        smtp_socket=smtp_socket,
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_username="testuser",
        smtp_password="secret",
    )

    assert result == {"status": "sent", "simulated": False}
    assert fake_client.entered is True
    assert fake_client.exited is True
    assert fake_client.starttls_hostname == "smtp.example.com"
    assert fake_client.login_args == ("testuser", "secret")
    assert fake_client.sent_message is message
    assert smtp_socket.fileno() == -1


def test_implicit_tls_smtp_client_keeps_original_tls_hostname():
    smtp_socket = _make_socket()
    try:
        client = _build_smtp_client(
            smtp_socket=smtp_socket,
            smtp_server="smtp.example.com",
            smtp_port=465,
        )

        assert client.sock is smtp_socket
        assert client.use_tls is True
        assert getattr(client, "_tls_server_hostname") == "smtp.example.com"
    finally:
        smtp_socket.close()


@pytest.mark.asyncio
async def test_send_email_raises_error_when_smtp_fails(monkeypatch):
    fake_client = FakeSmtpClient(fail_send=True)
    smtp_socket = _make_socket()

    async def fake_connect_validated_socket(*args, **kwargs):
        return smtp_socket

    def fake_build_client(**kwargs):
        return fake_client

    monkeypatch.setattr(
        "services.email_client._connect_validated_smtp_socket",
        fake_connect_validated_socket,
    )
    monkeypatch.setattr("services.email_client._build_smtp_client", fake_build_client)

    def fake_validate_smtp_destination(smtp_server, smtp_port, *, resolve_host=True):
        assert resolve_host is True
        return smtp_server, smtp_port

    monkeypatch.setattr(
        "services.email_client.validate_smtp_destination",
        fake_validate_smtp_destination,
    )

    with pytest.raises(Exception, match="Failed to send email"):
        await send_email(
            to_address="test@example.com",
            subject="Test Failure",
            body="Should fail because SMTP server is invalid",
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_username="testuser",
        )
    assert smtp_socket.fileno() == -1
