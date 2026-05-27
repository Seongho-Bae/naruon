import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Email, TenantConfig
from services.email_service import detect_reply_tracking
from services.threading_service import normalize_message_id
import datetime
import email.utils as email_utils

logger = logging.getLogger(__name__)


def configured_email_addresses(tenant_config: TenantConfig | None) -> set[str]:
    addresses = set()
    if tenant_config is None:
        return addresses
    for raw_address in (
        getattr(tenant_config, "smtp_username", None),
        getattr(tenant_config, "imap_username", None),
    ):
        _, parsed_address = email_utils.parseaddr(raw_address or "")
        normalized_address = parsed_address.strip().lower()
        if normalized_address:
            addresses.add(normalized_address)
    return addresses


def message_sender_address(email_message: Email) -> str:
    _, parsed_address = email_utils.parseaddr(email_message.sender or "")
    return parsed_address.strip().lower()


def message_recipient_addresses(email_message: Email) -> set[str]:
    return {
        parsed_address.strip().lower()
        for _, parsed_address in email_utils.getaddresses(
            [email_message.recipients or ""]
        )
        if parsed_address.strip()
    }


def message_is_from_user(email_message: Email, user_addresses: set[str]) -> bool:
    sender_address = message_sender_address(email_message)
    return bool(sender_address and sender_address in user_addresses)


def message_is_self_sent(email_message: Email, user_addresses: set[str]) -> bool:
    return message_is_from_user(email_message, user_addresses) and bool(
        message_recipient_addresses(email_message) & user_addresses
    )


def reply_tracking_thread_key(email_message: Email) -> str:
    normalized_key = normalize_message_id(email_message.thread_id) or normalize_message_id(
        email_message.message_id
    )
    return normalized_key or email_message.message_id


def thread_reply_candidate(
    thread_messages: list[Email], user_addresses: set[str]
) -> Email | None:
    if not user_addresses:
        return None

    candidates = []
    ordered_messages = sorted(thread_messages, key=lambda item: item.date)
    for sent_message in ordered_messages:
        if not message_is_from_user(sent_message, user_addresses):
            continue
        if message_is_self_sent(sent_message, user_addresses):
            continue
        if not detect_reply_tracking({"body": sent_message.body}):
            continue
        has_later_external_reply = any(
            not message_is_from_user(reply_message, user_addresses)
            and reply_message.date > sent_message.date
            for reply_message in ordered_messages
        )
        if not has_later_external_reply:
            candidates.append(sent_message)
    return candidates[-1] if candidates else None


def thread_requires_reply(
    thread_messages: list[Email], user_addresses: set[str]
) -> bool:
    return thread_reply_candidate(thread_messages, user_addresses) is not None


async def check_missing_replies(
    session: AsyncSession, user_id: str, organization_id: str | None
) -> list[Email]:
    """
    Checks for sent emails that expect a reply but haven't received one.
    Returns a list of such emails.
    """
    # Find user's own email address
    tenant_config = await session.execute(
        select(TenantConfig).where(TenantConfig.user_id == user_id)
    )
    config = tenant_config.scalar_one_or_none()
    user_addresses = configured_email_addresses(config)

    if not user_addresses:
        logger.info(f"Cannot track replies for {user_id} - no SMTP username configured")
        return []

    recent_limit = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=7
    )
    organization_filter = (
        Email.organization_id == organization_id
        if organization_id is not None
        else Email.organization_id.is_(None)
    )
    stmt = select(Email).where(
        Email.user_id == user_id,
        organization_filter,
        Email.date > recent_limit,
    ).order_by(Email.date.asc())
    result = await session.execute(stmt)
    emails = result.scalars().all()

    threads: dict[str, list[Email]] = {}
    for email_message in emails:
        threads.setdefault(reply_tracking_thread_key(email_message), []).append(
            email_message
        )

    flagged = []
    for thread_messages in threads.values():
        candidate = thread_reply_candidate(thread_messages, user_addresses)
        if candidate is not None:
            flagged.append(candidate)

    flagged.sort(key=lambda item: item.date, reverse=True)
    logger.info(f"Found {len(flagged)} emails awaiting replies for user {user_id}")
    return flagged
