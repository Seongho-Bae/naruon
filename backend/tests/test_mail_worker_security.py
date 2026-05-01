import asyncio

import pytest

from db.models import TenantConfig
from services.imap_worker import ImapSyncWorker
from services.pop3_worker import Pop3SyncWorker


class FakeImapClient:
    protocol = object()

    async def wait_hello_from_server(self):
        return None

    async def logout(self):
        return None


@pytest.mark.asyncio
async def test_imap_worker_rejects_private_host_before_connecting(monkeypatch):
    calls = []

    def fake_imap_ssl(host, port):
        calls.append((host, port))
        return FakeImapClient()

    monkeypatch.setattr("services.imap_worker.aioimaplib.IMAP4_SSL", fake_imap_ssl)

    await ImapSyncWorker()._sync_tenant(
        TenantConfig(user_id="alice", imap_server="127.0.0.1", imap_port=993)
    )

    assert calls == []


@pytest.mark.asyncio
async def test_imap_worker_connects_to_validated_resolved_ip(monkeypatch):
    calls = []

    def fake_getaddrinfo(*args, **kwargs):
        return [(2, 1, 6, "", ("93.184.216.34", 993))]

    def fake_imap_ssl(host, port):
        calls.append((host, port))
        return FakeImapClient()

    monkeypatch.setattr("services.mail_endpoint_policy.socket.getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr("services.imap_worker.aioimaplib.IMAP4_SSL", fake_imap_ssl)

    await ImapSyncWorker()._sync_tenant(
        TenantConfig(user_id="alice", imap_server="imap.example.com", imap_port=993)
    )

    assert calls == [("93.184.216.34", 993)]


@pytest.mark.asyncio
async def test_pop3_worker_rejects_private_host_before_connecting(monkeypatch):
    calls = []

    class FakePop3Client:
        def __init__(self, host, port):
            calls.append((host, port))

        def quit(self):
            return None

    monkeypatch.setattr("services.pop3_worker.poplib.POP3_SSL", FakePop3Client)

    await Pop3SyncWorker()._sync_tenant(
        TenantConfig(user_id="alice", pop3_server="127.0.0.1", pop3_port=995),
        asyncio.Semaphore(1),
    )

    assert calls == []


@pytest.mark.asyncio
async def test_pop3_worker_connects_to_validated_resolved_ip(monkeypatch):
    calls = []
    resolver_calls = []

    class FakePop3Client:
        def __init__(self, host, port):
            calls.append((host, port))

        def quit(self):
            return None

    def fake_getaddrinfo(*args, **kwargs):
        resolver_calls.append(args)
        if len(resolver_calls) > 1:
            raise AssertionError("POP3 worker must not re-resolve after pinning")
        return [(2, 1, 6, "", ("93.184.216.34", 995))]

    monkeypatch.setattr("services.mail_endpoint_policy.socket.getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr("services.pop3_worker.poplib.POP3_SSL", FakePop3Client)

    await Pop3SyncWorker()._sync_tenant(
        TenantConfig(user_id="alice", pop3_server="pop3.example.com", pop3_port=995),
        asyncio.Semaphore(1),
    )

    assert calls == [("93.184.216.34", 995)]
    assert len(resolver_calls) == 1
