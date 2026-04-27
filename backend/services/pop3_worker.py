import asyncio
import logging
import poplib
from core.config import settings

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
        logger.info(f"Connecting to POP3 server {settings.POP3_SERVER}:{settings.POP3_PORT}")
        try:
            # We use asyncio.to_thread for synchronous poplib
            await asyncio.to_thread(self._do_pop3_sync)
            logger.info("Successfully connected to POP3 server.")
            
        except Exception as e:
            logger.error(f"Failed to connect or sync with POP3 server: {e}")
            raise

    def _do_pop3_sync(self):
        pop3_client = poplib.POP3_SSL(settings.POP3_SERVER, settings.POP3_PORT)
        try:
            # Note: Real implementation would use OAuth or password.
            # pop3_client.user(settings.POP3_USERNAME)
            # pop3_client.pass_(settings.POP3_PASSWORD)
            pass
        finally:
            pop3_client.quit()
