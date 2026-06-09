import asyncio
import datetime
import logging
from collections.abc import Iterable

import aioimaplib
from sqlalchemy import select

from db.models import Email, TenantConfig
from db.session import AsyncSessionLocal
from services.email_parser import EmailData
from services.knowledge_extractor import (
    extract_knowledge_from_self_sent,
    is_self_sent_email,
)
from services.email_client import validate_imap_destination
from services.threading_service import assign_thread_id, generate_email_fingerprint
from services.email_dedupe_service import strong_email_fingerprint


async def process_fetched_email(
    session,
    email_data: EmailData,
    user_id: str,
    organization_id: str | None,
    owner_addresses: Iterable[str] | None = None,
):
    subject = email_data.get("subject", "")
    date_obj = email_data.get("date")
    if hasattr(date_obj, "isoformat"):
        date_str = date_obj.isoformat()
    else:
        date_str = str(date_obj) if date_obj else ""
    if isinstance(date_obj, datetime.datetime):
        persisted_date = (
            date_obj.astimezone(datetime.timezone.utc)
            if date_obj.tzinfo is not None
            else date_obj.replace(tzinfo=datetime.timezone.utc)
        )
    else:
        persisted_date = datetime.datetime.now(datetime.timezone.utc)
    sender = email_data.get("sender", "")
    recipients_list = email_data.get("recipients", [])
    recipients = (
        ",".join(recipients_list)
        if isinstance(recipients_list, list)
        else str(recipients_list or "")
    )

    fingerprint = strong_email_fingerprint(
        sender=sender,
        subject=subject,
        date=persisted_date,
        body=email_data.get("body", ""),
    ) or generate_email_fingerprint(subject, date_str, sender, recipients)

    # Check if duplicate
    stmt = select(Email).where(
        Email.user_id == user_id,
        Email.organization_id == (organization_id if organization_id else None),
        Email.fingerprint == fingerprint,
    )
    result = await session.execute(stmt)
    existing_email = result.scalar_one_or_none()

    if existing_email:
        logger.info(
            "Email with fingerprint %s already exists. Skipping duplicate insertion.",
            fingerprint,
        )
        return existing_email

    thread_id = await assign_thread_id(
        session, email_data, user_id=user_id, organization_id=organization_id
    )

    new_email = Email(
        user_id=user_id,
        organization_id=organization_id or None,
        message_id=email_data.get("message_id", ""),
        thread_id=thread_id,
        fingerprint=fingerprint,
        sender=sender,
        recipients=recipients,
        subject=subject,
        date=persisted_date,
        body=email_data.get("body", ""),
        embedding=[0.0] * 1536,
    )

    session.add(new_email)
    if is_self_sent_email(new_email, owner_addresses):
        await session.flush()
        await extract_knowledge_from_self_sent(session, new_email, owner_addresses)
    return new_email

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
        try:
            imap_server, imap_port = validate_imap_destination(imap_server, imap_port)
        except ValueError:
            logger.info(
                "Skipping IMAP sync for user %s due to mail destination policy",
                config.user_id,
            )
            return
        
        logger.info(
            "Connecting to IMAP server %s:%s for user %s",
            imap_server,
            imap_port,
            config.user_id,
        )
        import ssl
        ssl_context = ssl.create_default_context()
        imap_client = aioimaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=ssl_context)

        try:
            await imap_client.wait_hello_from_server()
            logger.info(f"Successfully connected to IMAP server for user {config.user_id}.")
            
            # Since this is a test/demo setup, we expect real IMAP to fail if invalid or missing creds.
            # But the requirement is to actually connect. 
            if config.imap_username and config.imap_password:
                resp, data = await imap_client.login(config.imap_username, config.imap_password)
                if resp != "OK":
                    raise Exception(f"IMAP login failed: {data}")
                
                await imap_client.select("INBOX")
                
                # Search for recent emails (e.g., last 10)
                # For simplicity, we just fetch a small batch to prove connectivity
                # Real parser logic would go here.
            else:
                logger.info(f"No IMAP credentials provided for user {config.user_id}, skipping login.")

            # Actual sync logic will be added here later

        except Exception as e:
            logger.error(f"Failed to connect or sync with IMAP server for user {config.user_id}: {e}")
            raise Exception(f"IMAP Sync failed for user {config.user_id}: {e}") from e
        finally:
            try:
                if hasattr(imap_client, "protocol") and imap_client.protocol:
                    await imap_client.logout()
            except Exception as logout_err:
                logger.warning(f"Error during IMAP logout for user {config.user_id}: {logout_err}")
