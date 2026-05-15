import socket
import ssl
import pytest
from unittest.mock import AsyncMock, patch

from db.models import MailboxAccount
from services import pop3_worker
from services.mail_server_security import MailServerConnectTarget
from services.pop3_worker import Pop3SyncWorker


class MockResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class MockSession:
    def __init__(self, accounts):
        self.accounts = accounts

    async def execute(self, _query):
        return MockResult(self.accounts)


class MockSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_pop3_worker_sync_mailbox_account_raises_when_invalid_server():
    worker = Pop3SyncWorker()
    account = MailboxAccount(
        user_id="testuser",
        email_address="alpha@example.com",
        display_name="Alpha",
        provider="custom",
        is_default_reply=True,
        is_active=True,
        pop3_server="invalid.example.com",
        pop3_port=995,
    )

    with pytest.raises(
        Exception, match="POP3 Sync failed for user testuser mailbox alpha@example.com"
    ):
        await worker._sync_mailbox_account(account, AsyncMock())


@pytest.mark.asyncio
async def test_pop3_worker_sync_enumerates_active_mailbox_accounts_with_pop3_server(
    monkeypatch,
):
    worker = Pop3SyncWorker()
    accounts = [
        MailboxAccount(
            id=1,
            user_id="testuser",
            email_address="alpha@example.com",
            display_name="Alpha",
            provider="custom",
            is_default_reply=True,
            is_active=True,
            pop3_server="pop.alpha.example.com",
            pop3_port=995,
        ),
        MailboxAccount(
            id=2,
            user_id="testuser",
            email_address="beta@example.com",
            display_name="Beta",
            provider="custom",
            is_default_reply=False,
            is_active=False,
            pop3_server="pop.beta.example.com",
            pop3_port=995,
        ),
        MailboxAccount(
            id=3,
            user_id="testuser",
            email_address="gamma@example.com",
            display_name="Gamma",
            provider="custom",
            is_default_reply=False,
            is_active=True,
            pop3_server=None,
            pop3_port=995,
        ),
    ]

    monkeypatch.setattr(
        "services.pop3_worker.AsyncSessionLocal",
        lambda: MockSessionContext(MockSession(accounts)),
    )
    sync_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(worker, "_sync_mailbox_account", sync_mock)

    await worker._sync()

    sync_mock.assert_awaited_once()
    assert sync_mock.await_args_list[0].args[0].email_address == "alpha@example.com"


def test_pop3_sync_uses_bounded_timeout(monkeypatch):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "pop.alpha.example.com"
        assert port == 995
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.216.34", port),
            )
        ]

    class FakePop3Client:
        def quit(self):
            return None

    calls = []

    def fake_create_client(target, timeout):
        calls.append((target.host, target.connect_host, target.port, timeout))
        return FakePop3Client()

    monkeypatch.setattr(
        "services.mail_server_security.socket.getaddrinfo", fake_getaddrinfo
    )
    monkeypatch.setattr(
        "services.pop3_worker._create_pop3_ssl_client", fake_create_client
    )

    worker = Pop3SyncWorker()
    account = MailboxAccount(
        user_id="testuser",
        email_address="alpha@example.com",
        display_name="Alpha",
        provider="custom",
        is_default_reply=True,
        is_active=True,
        pop3_server="pop.alpha.example.com",
        pop3_port=995,
    )

    worker._do_pop3_sync(account)

    assert calls == [("pop.alpha.example.com", "93.184.216.34", 995, 15)]


def test_pop3_sync_uses_validated_connect_ip(monkeypatch):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "pop.public.example.com"
        assert port == 995
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.216.34", port),
            )
        ]

    class FakePop3Client:
        def quit(self):
            return None

    calls = []

    def fake_create_client(target, timeout):
        calls.append((target.host, target.connect_host, target.port, timeout))
        return FakePop3Client()

    monkeypatch.setattr(
        "services.mail_server_security.socket.getaddrinfo", fake_getaddrinfo
    )
    monkeypatch.setattr(
        "services.pop3_worker._create_pop3_ssl_client",
        fake_create_client,
        raising=False,
    )

    worker = Pop3SyncWorker()
    account = MailboxAccount(
        user_id="testuser",
        email_address="alpha@example.com",
        display_name="Alpha",
        provider="custom",
        is_default_reply=True,
        is_active=True,
        pop3_server="pop.public.example.com",
        pop3_port=995,
    )

    with patch("services.pop3_worker.poplib.POP3_SSL") as pop3_ssl:
        worker._do_pop3_sync(account)

    assert calls == [("pop.public.example.com", "93.184.216.34", 995, 15)]
    pop3_ssl.assert_not_called()


def test_pop3_pinned_client_uses_verifying_tls_context(monkeypatch):
    calls = []

    class FakePinnedPOP3:
        def __init__(self, host, port, connect_host, timeout, context):
            calls.append((host, port, connect_host, timeout, context))

    monkeypatch.setattr(pop3_worker, "_PinnedPOP3_SSL", FakePinnedPOP3)

    pop3_worker._create_pop3_ssl_client(
        MailServerConnectTarget(
            host="pop.public.example.com",
            port=995,
            connect_host="93.184.216.34",
        ),
        timeout=15,
    )

    context = calls[0][4]
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_pop3_sync_revalidates_host_resolution_before_connecting(monkeypatch):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "pop.rebind.example.com"
        assert port == 995
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

    worker = Pop3SyncWorker()
    account = MailboxAccount(
        user_id="testuser",
        email_address="alpha@example.com",
        display_name="Alpha",
        provider="custom",
        is_default_reply=True,
        is_active=True,
        pop3_server="pop.rebind.example.com",
        pop3_port=995,
    )

    with patch("services.pop3_worker.poplib.POP3_SSL") as pop3_ssl:
        with pytest.raises(Exception, match="내부 네트워크"):
            worker._do_pop3_sync(account)

    pop3_ssl.assert_not_called()
