import asyncio
import logging
import ssl
from typing import cast

import aioimaplib
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import MailboxAccount
from services.mail_server_security import (
    MailServerConnectTarget,
    MailServerValidationError,
    resolve_mail_server_connect_target,
)

logger = logging.getLogger(__name__)


class _PinnedIMAP4_SSL(aioimaplib.IMAP4_SSL):
    def __init__(
        self,
        host: str,
        port: int,
        connect_host: str,
        loop: asyncio.AbstractEventLoop | None = None,
        timeout: float = aioimaplib.IMAP4.TIMEOUT_SECONDS,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self._connect_host = connect_host
        super().__init__(host, port, loop, timeout, ssl_context)

    def create_client(
        self,
        host: str,
        port: int,
        loop: asyncio.AbstractEventLoop | None,
        conn_lost_cb=None,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        if ssl_context is None:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        local_loop = loop if loop is not None else asyncio.get_running_loop()
        self.protocol = aioimaplib.IMAP4ClientProtocol(local_loop, conn_lost_cb)
        local_loop.create_task(
            local_loop.create_connection(
                lambda: self.protocol,
                self._connect_host,
                port,
                ssl=ssl_context,
                server_hostname=host,
            )
        )


def _create_imap_ssl_client(target: MailServerConnectTarget):
    return _PinnedIMAP4_SSL(target.host, target.port, target.connect_host)


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
            accounts = await session.execute(
                select(MailboxAccount).where(
                    MailboxAccount.is_active.is_(True),
                    MailboxAccount.imap_server.isnot(None),
                )
            )

        tasks = []
        for account in accounts.scalars().all():
            if (
                not account.is_active
                or not account.imap_server
                or not account.imap_port
            ):
                continue
            tasks.append(self._sync_mailbox_account(account))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_mailbox_account(self, account: MailboxAccount):
        # Already verified not None in caller
        if not account.imap_server or not account.imap_port:
            raise Exception(
                f"IMAP Sync failed for user {account.user_id} mailbox {account.email_address}: IMAP server/port missing"
            )
        imap_server = str(account.imap_server)
        imap_port = cast(int, account.imap_port)

        try:
            target = resolve_mail_server_connect_target(
                "imap", "IMAP", imap_server, imap_port
            )
        except MailServerValidationError as exc:
            raise Exception(
                f"IMAP Sync failed for user {account.user_id} mailbox {account.email_address}: {exc}"
            ) from exc

        logger.info(
            f"Connecting to IMAP server {target.host}:{target.port} for user {account.user_id} mailbox {account.email_address}"
        )
        imap_client = _create_imap_ssl_client(target)

        try:
            await imap_client.wait_hello_from_server()
            logger.info(
                f"Successfully connected to IMAP server for user {account.user_id} mailbox {account.email_address}."
            )

            # Since this is a test/demo setup, we expect real IMAP to fail if invalid or missing creds.
            # But the requirement is to actually connect.
            if account.imap_username and account.imap_password:
                resp, data = await imap_client.login(
                    account.imap_username, account.imap_password
                )
                if resp != "OK":
                    raise Exception(f"IMAP login failed: {data}")

                await imap_client.select("INBOX")

                # Search for recent emails (e.g., last 10)
                # For simplicity, we just fetch a small batch to prove connectivity
                # Real parser logic would go here.
            else:
                logger.info(
                    f"No IMAP credentials provided for user {account.user_id} mailbox {account.email_address}, skipping login."
                )

            # Actual sync logic will be added here later

        except Exception as e:
            logger.error(
                f"Failed to connect or sync with IMAP server for user {account.user_id} mailbox {account.email_address}: {e}"
            )
            raise Exception(
                f"IMAP Sync failed for user {account.user_id} mailbox {account.email_address}: {e}"
            ) from e
        finally:
            try:
                if hasattr(imap_client, "protocol") and imap_client.protocol:
                    await imap_client.logout()
            except Exception as logout_err:
                logger.warning(
                    f"Error during IMAP logout for user {account.user_id} mailbox {account.email_address}: {logout_err}"
                )
