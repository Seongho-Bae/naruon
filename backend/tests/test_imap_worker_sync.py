import pytest
from db.models import TenantConfig
from services.imap_worker import ImapSyncWorker

@pytest.mark.asyncio
async def test_imap_worker_sync_tenant_raises_when_invalid_server():
    worker = ImapSyncWorker()
    config = TenantConfig(
        user_id="testuser",
        imap_server="invalid.example.com",
        imap_port=993
    )
    
    with pytest.raises(Exception, match="IMAP Sync failed for user testuser"):
        await worker._sync_tenant(config)

