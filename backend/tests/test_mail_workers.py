import asyncio

import pytest

import services.imap_worker as imap_worker_module
import services.pop3_worker as pop3_worker_module
from db.models import TenantConfig
from services.imap_worker import ImapSyncWorker
from services.pop3_worker import Pop3SyncWorker


def make_mail_config() -> TenantConfig:
    return TenantConfig(
        user_id="default",
        imap_server="8.8.8.8",
        imap_port=993,
        pop3_server="8.8.8.8",
        pop3_port=995,
    )


@pytest.mark.asyncio
async def test_imap_worker_validates_target_without_opening_network_connection():
    worker = ImapSyncWorker()

    await worker._sync_tenant(make_mail_config())

    assert not hasattr(imap_worker_module, "aioimaplib")


@pytest.mark.asyncio
async def test_pop3_worker_validates_target_without_opening_network_connection():
    worker = Pop3SyncWorker()

    await worker._sync_tenant(make_mail_config(), asyncio.Semaphore(1))

    assert not hasattr(pop3_worker_module, "poplib")
