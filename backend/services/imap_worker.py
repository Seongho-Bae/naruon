import asyncio
import logging

from sqlalchemy import select

from core.network_targets import MailTargetValidationError, validate_mail_server_target
from db.models import TenantConfig
from db.session import AsyncSessionLocal

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
            configs = await session.execute(
                select(TenantConfig).where(TenantConfig.imap_server.isnot(None))
            )

        tasks = []
        for config in configs.scalars():
            if not config.imap_server or not config.imap_port:
                continue
            tasks.append(self._sync_tenant(config))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_tenant(self, config: TenantConfig):
        try:
            imap_server, imap_port = validate_mail_server_target(
                config.imap_server, config.imap_port, "imap"
            )
        except MailTargetValidationError:
            logger.warning("Skipping unsafe IMAP server for user %s", config.user_id)
            return

        logger.info(
            "Validated IMAP server %s:%s for user %s; sync is simulated until "
            "real sync can pin DNS results safely.",
            imap_server,
            imap_port,
            config.user_id,
        )
