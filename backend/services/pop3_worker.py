import asyncio
import logging

from sqlalchemy import select

from core.network_targets import MailTargetValidationError, validate_mail_server_target
from db.models import TenantConfig
from db.session import AsyncSessionLocal

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
            configs = await session.execute(
                select(TenantConfig).where(TenantConfig.pop3_server.isnot(None))
            )

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
            try:
                pop3_server, pop3_port = validate_mail_server_target(
                    config.pop3_server, config.pop3_port, "pop3"
                )
            except MailTargetValidationError:
                logger.warning(
                    "Skipping unsafe POP3 server for user %s", config.user_id
                )
                return
            logger.info(
                "Validated POP3 server %s:%s for user %s; sync is simulated until "
                "real sync can pin DNS results safely.",
                pop3_server,
                pop3_port,
                config.user_id,
            )
