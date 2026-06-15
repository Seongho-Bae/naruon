import pytest
from db.models import TenantConfig
from services.imap_worker import ImapSyncWorker

@pytest.mark.asyncio
async def test_imap_worker_skips_disallowed_destination(monkeypatch):
    worker = ImapSyncWorker()
    config = TenantConfig(
        user_id="testuser",
        imap_server="127.0.0.1",
        imap_port=993,
    )
    connection_attempts = []

    def fail_connect(*args, **kwargs):
        connection_attempts.append((args, kwargs))
        raise AssertionError("IMAP connection must not open before policy validation")

    monkeypatch.setattr("services.imap_worker.aioimaplib.IMAP4_SSL", fail_connect)

    await worker._sync_tenant(config)

    assert connection_attempts == []


@pytest.mark.asyncio
async def test_imap_worker_sync_tenant_raises_when_connection_fails(monkeypatch):
    worker = ImapSyncWorker()
    config = TenantConfig(
        user_id="testuser",
        imap_server="imap.example.com",
        imap_port=993,
    )

    class FailingImapClient:
        protocol = None

        async def wait_hello_from_server(self):
            raise RuntimeError("connect failed")

    monkeypatch.setattr(
        "services.imap_worker.validate_imap_destination",
        lambda host, port: (host, port),
    )
    monkeypatch.setattr(
        "services.imap_worker.aioimaplib.IMAP4_SSL",
        lambda host, port, **kwargs: FailingImapClient(),
    )

    with pytest.raises(Exception, match="IMAP Sync failed for user testuser"):
        await worker._sync_tenant(config)


@pytest.mark.asyncio
async def test_imap_worker_imports_fetched_rfc822_messages(monkeypatch):
    worker = ImapSyncWorker()
    config = TenantConfig(
        user_id="imap-user",
        organization_id="org-imap",
        imap_server="imap.example.com",
        imap_port=993,
        imap_username="imap-user@example.com",
        imap_password="imap-secret",
    )
    raw_message = (
        b"Message-ID: <imap-1@example.com>\r\n"
        b"From: Sender <sender@example.com>\r\n"
        b"To: imap-user@example.com\r\n"
        b"Subject: IMAP import\r\n"
        b"Date: Mon, 15 Jun 2026 10:00:00 +0000\r\n"
        b"\r\n"
        b"Imported from IMAP.\r\n"
    )

    class FakeImapClient:
        protocol = object()

        def __init__(self):
            self.fetch_calls = []
            self.logged_out = False

        async def wait_hello_from_server(self):
            return None

        async def login(self, username, secret):
            assert username == "imap-user@example.com"
            assert secret == "imap-secret"
            return "OK", [b"logged in"]

        async def select(self, mailbox):
            assert mailbox == "INBOX"
            return "OK", [b"selected"]

        async def search(self, criteria):
            assert criteria == "ALL"
            return "OK", [b"1"]

        async def fetch(self, message_number, query):
            self.fetch_calls.append((message_number, query))
            return "OK", [(b"1 (RFC822 {%d}" % len(raw_message), raw_message)]

        async def logout(self):
            self.logged_out = True

    imap_client = FakeImapClient()
    imported = []

    class FakeSession:
        def __init__(self):
            self.committed = False
            self.rolled_back = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def commit(self):
            self.committed = True

        async def rollback(self):
            self.rolled_back = True

    session = FakeSession()

    async def fake_process_fetched_email(
        db_session, email_data, user_id, organization_id, owner_addresses=None
    ):
        imported.append(
            {
                "session": db_session,
                "email_data": email_data,
                "user_id": user_id,
                "organization_id": organization_id,
                "owner_addresses": owner_addresses,
            }
        )

    monkeypatch.setattr(
        "services.imap_worker.validate_imap_destination",
        lambda host, port: (host, port),
    )
    monkeypatch.setattr(
        "services.imap_worker.aioimaplib.IMAP4_SSL",
        lambda host, port, **kwargs: imap_client,
    )
    monkeypatch.setattr("services.imap_worker.AsyncSessionLocal", lambda: session)
    monkeypatch.setattr(
        "services.imap_worker.process_fetched_email",
        fake_process_fetched_email,
        raising=False,
    )

    imported_count = await worker._sync_tenant(config)

    assert imported_count == 1
    assert imap_client.fetch_calls == [("1", "(RFC822)")]
    assert imap_client.logged_out is True
    assert len(imported) == 1
    assert imported[0]["session"] is session
    assert imported[0]["user_id"] == "imap-user"
    assert imported[0]["organization_id"] == "org-imap"
    assert imported[0]["owner_addresses"] == ["imap-user@example.com"]
    assert imported[0]["email_data"]["message_id"] == "<imap-1@example.com>"
    assert imported[0]["email_data"]["subject"] == "IMAP import"
    assert session.committed is True
    assert session.rolled_back is False


@pytest.mark.asyncio
async def test_imap_worker_requires_credentials_without_sensitive_log_names(
    caplog, monkeypatch
):
    worker = ImapSyncWorker()
    config = TenantConfig(
        user_id="imap-user",
        imap_server="imap.example.com",
        imap_port=993,
    )

    class FakeImapClient:
        protocol = object()

        async def wait_hello_from_server(self):
            return None

        async def logout(self):
            return None

    monkeypatch.setattr(
        "services.imap_worker.validate_imap_destination",
        lambda host, port: (host, port),
    )
    monkeypatch.setattr(
        "services.imap_worker.aioimaplib.IMAP4_SSL",
        lambda host, port, **kwargs: FakeImapClient(),
    )

    with pytest.raises(Exception, match="IMAP Sync failed for user imap-user"):
        await worker._sync_tenant(config)

    assert "imap_password" not in caplog.text
    assert "password" not in caplog.text.lower()
    assert "imap-secret" not in caplog.text
