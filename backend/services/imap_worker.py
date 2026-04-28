import asyncio
import logging
import aioimaplib
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import TenantConfig

logger = logging.getLogger(__name__)


class ImapSyncWorker:
    def __init__(self):
        self._task = None
        self._is_running = False

    async def start(self):
        if self._is_running:
            logger.warning("ImapSyncWorker is already running.")
            return

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("ImapSyncWorker started.")

    async def stop(self):
        if not self._is_running:
            return

        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ImapSyncWorker stopped.")

    async def _run_loop(self):
        while self._is_running:
            try:
                await self._sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ImapSyncWorker loop: {e}", exc_info=True)

            # Sleep for 1 minute before the next sync
            if self._is_running:
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    break

    async def _sync(self):
        async with AsyncSessionLocal() as session:
            configs = await session.execute(select(TenantConfig).where(TenantConfig.imap_server.isnot(None)))
            
        tasks = []
        for config in configs.scalars():
            if not config.imap_server or not config.imap_port:
                continue
            tasks.append(self._sync_tenant(config))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_tenant(self, config: TenantConfig):
        # Already verified not None in caller
        imap_server = str(config.imap_server)
        imap_port = int(config.imap_port)  # type: ignore
        
        logger.info(
            f"Connecting to IMAP server {imap_server}:{imap_port} for user {config.user_id}"
        )
        imap_client = aioimaplib.IMAP4_SSL(imap_server, imap_port)

        try:
            await imap_client.wait_hello_from_server()
            logger.info(f"Successfully connected to IMAP server for user {config.user_id}.")

            # Actual sync logic will be added here later

        except Exception as e:
            logger.error(f"Failed to connect or sync with IMAP server for user {config.user_id}: {e}")
        finally:
            try:
                if hasattr(imap_client, "protocol") and imap_client.protocol:
                    await imap_client.logout()
            except Exception as logout_err:
                logger.warning(f"Error during IMAP logout for user {config.user_id}: {logout_err}")
