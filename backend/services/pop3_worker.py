import asyncio
import logging
import poplib
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import TenantConfig

logger = logging.getLogger(__name__)


class Pop3SyncWorker:
    def __init__(self):
        self._task = None
        self._is_running = False

    async def start(self):
        if self._is_running:
            logger.warning("Pop3SyncWorker is already running.")
            return

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Pop3SyncWorker started.")

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
        logger.info("Pop3SyncWorker stopped.")

    async def _run_loop(self):
        while self._is_running:
            try:
                await self._sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Pop3SyncWorker loop: {e}", exc_info=True)

            if self._is_running:
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    break

    async def _sync(self):
        async with AsyncSessionLocal() as session:
            configs = await session.execute(select(TenantConfig).where(TenantConfig.pop3_server.isnot(None)))
            
        semaphore = asyncio.Semaphore(10)
        tasks = []
        for config in configs.scalars():
            if not config.pop3_server or not config.pop3_port:
                continue
            tasks.append(self._sync_tenant(config, semaphore))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_tenant(self, config: TenantConfig, semaphore: asyncio.Semaphore):
        async with semaphore:
            pop3_server = str(config.pop3_server)
            pop3_port = int(config.pop3_port)  # type: ignore
            logger.info(
                f"Connecting to POP3 server {pop3_server}:{pop3_port} for user {config.user_id}"
            )
            try:
                # We use asyncio.to_thread for synchronous poplib
                await asyncio.to_thread(self._do_pop3_sync, config)
                logger.info(f"Successfully connected to POP3 server for user {config.user_id}.")
            except Exception as e:
                logger.error(f"Failed to connect or sync with POP3 server for user {config.user_id}: {e}")

    def _do_pop3_sync(self, config: TenantConfig):
        pop3_server = str(config.pop3_server)
        pop3_port = int(config.pop3_port)  # type: ignore
        pop3_client = poplib.POP3_SSL(pop3_server, pop3_port)
        try:
            # Note: Real implementation would use OAuth or password.
            # pop3_client.user(config.pop3_username)
            # pop3_client.pass_(config.pop3_password)
            pass
        finally:
            pop3_client.quit()
