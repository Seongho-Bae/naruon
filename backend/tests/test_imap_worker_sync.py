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
        lambda host, port: FailingImapClient(),
    )

    with pytest.raises(Exception, match="IMAP Sync failed for user testuser"):
        await worker._sync_tenant(config)
