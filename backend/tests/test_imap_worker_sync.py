import socket
import pytest
from unittest.mock import AsyncMock, patch

from db.models import MailboxAccount
from services.imap_worker import ImapSyncWorker


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
async def test_imap_worker_sync_mailbox_account_raises_when_invalid_server():
    worker = ImapSyncWorker()
    account = MailboxAccount(
        user_id="testuser",
        email_address="alpha@example.com",
        display_name="Alpha",
        provider="custom",
        is_default_reply=True,
        is_active=True,
        imap_server="invalid.example.com",
        imap_port=993,
    )

    with pytest.raises(
        Exception, match="IMAP Sync failed for user testuser mailbox alpha@example.com"
    ):
        await worker._sync_mailbox_account(account)


@pytest.mark.asyncio
async def test_imap_worker_revalidates_host_resolution_before_connecting(monkeypatch):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "imap.rebind.example.com"
        assert port == 993
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

    worker = ImapSyncWorker()
    account = MailboxAccount(
        user_id="testuser",
        email_address="alpha@example.com",
        display_name="Alpha",
        provider="custom",
        is_default_reply=True,
        is_active=True,
        imap_server="imap.rebind.example.com",
        imap_port=993,
    )

    with patch("services.imap_worker.aioimaplib.IMAP4_SSL") as imap_ssl:
        with pytest.raises(Exception, match="내부 네트워크"):
            await worker._sync_mailbox_account(account)

    imap_ssl.assert_not_called()


@pytest.mark.asyncio
async def test_imap_worker_uses_validated_connect_ip(monkeypatch):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "imap.public.example.com"
        assert port == 993
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.216.34", port),
            )
        ]

    class FakeImapClient:
        protocol = object()

        async def wait_hello_from_server(self):
            return None

        async def logout(self):
            return None

    calls = []

    def fake_create_client(target):
        calls.append((target.host, target.connect_host, target.port))
        return FakeImapClient()

    monkeypatch.setattr(
        "services.mail_server_security.socket.getaddrinfo", fake_getaddrinfo
    )
    monkeypatch.setattr(
        "services.imap_worker._create_imap_ssl_client",
        fake_create_client,
        raising=False,
    )

    worker = ImapSyncWorker()
    account = MailboxAccount(
        user_id="testuser",
        email_address="alpha@example.com",
        display_name="Alpha",
        provider="custom",
        is_default_reply=True,
        is_active=True,
        imap_server="imap.public.example.com",
        imap_port=993,
    )

    with patch("services.imap_worker.aioimaplib.IMAP4_SSL") as imap_ssl:
        await worker._sync_mailbox_account(account)

    assert calls == [("imap.public.example.com", "93.184.216.34", 993)]
    imap_ssl.assert_not_called()


@pytest.mark.asyncio
async def test_imap_worker_sync_enumerates_active_mailbox_accounts_with_imap_server(
    monkeypatch,
):
    worker = ImapSyncWorker()
    accounts = [
        MailboxAccount(
            id=1,
            user_id="testuser",
            email_address="alpha@example.com",
            display_name="Alpha",
            provider="custom",
            is_default_reply=True,
            is_active=True,
            imap_server="imap.alpha.example.com",
            imap_port=993,
        ),
        MailboxAccount(
            id=2,
            user_id="testuser",
            email_address="beta@example.com",
            display_name="Beta",
            provider="custom",
            is_default_reply=False,
            is_active=False,
            imap_server="imap.beta.example.com",
            imap_port=993,
        ),
        MailboxAccount(
            id=3,
            user_id="testuser",
            email_address="gamma@example.com",
            display_name="Gamma",
            provider="custom",
            is_default_reply=False,
            is_active=True,
            imap_server=None,
            imap_port=993,
        ),
    ]

    monkeypatch.setattr(
        "services.imap_worker.AsyncSessionLocal",
        lambda: MockSessionContext(MockSession(accounts)),
    )
    sync_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(worker, "_sync_mailbox_account", sync_mock)

    await worker._sync()

    sync_mock.assert_awaited_once()
    assert sync_mock.await_args_list[0].args[0].email_address == "alpha@example.com"
