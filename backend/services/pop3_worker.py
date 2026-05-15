import asyncio
import logging
import socket
import ssl
from typing import cast

import poplib
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import MailboxAccount
from services.mail_server_security import (
    MailServerConnectTarget,
    MailServerValidationError,
    resolve_mail_server_connect_target,
)

logger = logging.getLogger(__name__)


class _PinnedPOP3_SSL(poplib.POP3_SSL):
    def __init__(
        self,
        host: str,
        port: int,
        connect_host: str,
        timeout: float | int | None = None,
        context: ssl.SSLContext | None = None,
    ) -> None:
        self._connect_host = connect_host
        self._ssl_context = context or ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH
        )
        super().__init__(host, port, timeout=timeout, context=self._ssl_context)

    def _create_socket(self, timeout):
        if timeout is not None and not timeout:
            raise ValueError("Non-blocking socket (timeout=0) is not supported")
        sock = socket.create_connection((self._connect_host, self.port), timeout)
        return self._ssl_context.wrap_socket(sock, server_hostname=self.host)


def _create_pop3_ssl_client(target: MailServerConnectTarget, timeout: int):
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    return _PinnedPOP3_SSL(
        target.host,
        target.port,
        target.connect_host,
        timeout=timeout,
        context=context,
    )


class Pop3SyncWorker:
    SOCKET_TIMEOUT_SECONDS = 15

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
            accounts = await session.execute(
                select(MailboxAccount).where(
                    MailboxAccount.is_active.is_(True),
                    MailboxAccount.pop3_server.isnot(None),
                )
            )

        semaphore = asyncio.Semaphore(10)
        tasks = []
        for account in accounts.scalars().all():
            if (
                not account.is_active
                or not account.pop3_server
                or not account.pop3_port
            ):
                continue
            tasks.append(self._sync_mailbox_account(account, semaphore))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_mailbox_account(
        self, account: MailboxAccount, semaphore: asyncio.Semaphore
    ):
        async with semaphore:
            if not account.pop3_server or not account.pop3_port:
                raise Exception(
                    f"POP3 Sync failed for user {account.user_id} mailbox {account.email_address}: POP3 server/port missing"
                )
            pop3_server = str(account.pop3_server)
            pop3_port = cast(int, account.pop3_port)
            logger.info(
                f"Connecting to POP3 server {pop3_server}:{pop3_port} for user {account.user_id} mailbox {account.email_address}"
            )
            try:
                # We use asyncio.to_thread for synchronous poplib
                await asyncio.to_thread(self._do_pop3_sync, account)
                logger.info(
                    f"Successfully connected to POP3 server for user {account.user_id} mailbox {account.email_address}."
                )
            except Exception as e:
                logger.error(
                    f"Failed to connect or sync with POP3 server for user {account.user_id} mailbox {account.email_address}: {e}"
                )
                raise Exception(
                    f"POP3 Sync failed for user {account.user_id} mailbox {account.email_address}: {e}"
                ) from e

    def _resolve_pop3_target(self, account: MailboxAccount) -> MailServerConnectTarget:
        if not account.pop3_server or not account.pop3_port:
            raise Exception(
                f"POP3 Sync failed for user {account.user_id} mailbox {account.email_address}: POP3 server/port missing"
            )
        pop3_server = str(account.pop3_server)
        pop3_port = cast(int, account.pop3_port)
        try:
            return resolve_mail_server_connect_target(
                "pop3", "POP3", pop3_server, pop3_port
            )
        except MailServerValidationError as exc:
            raise Exception(
                f"POP3 Sync failed for user {account.user_id} mailbox {account.email_address}: {exc}"
            ) from exc

    def _do_pop3_sync(self, account: MailboxAccount):
        target = self._resolve_pop3_target(account)
        pop3_client = _create_pop3_ssl_client(
            target, timeout=self.SOCKET_TIMEOUT_SECONDS
        )
        try:
            # Note: Real implementation would use OAuth or password.
            # pop3_client.user(account.pop3_username)
            # pop3_client.pass_(account.pop3_password)
            pass
        finally:
            pop3_client.quit()
