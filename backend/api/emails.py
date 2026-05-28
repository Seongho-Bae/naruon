from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from db.session import get_db
from db.models import Email
from pydantic import BaseModel, EmailStr, Field
import datetime
from typing import Literal
from services.email_client import EmailMessageParams, SmtpConfig, send_email, validate_smtp_destination
from services.reply_tracking_service import (
    check_missing_replies,
    configured_email_addresses,
    message_is_from_user,
    message_is_self_sent,
    thread_requires_reply,
)
from services.threading_service import normalize_message_id
from services.email_dedupe_service import (
    EmailDedupeCandidate,
    candidate_message_lookup_values,
    candidate_strong_fingerprint,
    email_strong_fingerprint,
)
import logging
from api.auth import AuthContext, get_auth_context
from services.tenant_config_scope import get_scoped_tenant_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails")


def canonical_thread_key(email: Email) -> str:
    return (
        normalize_message_id(email.thread_id)
        or normalize_message_id(email.message_id)
        or email.message_id
    )


def thread_lookup_values(thread_id: str) -> list[str]:
    normalized = normalize_message_id(thread_id) or thread_id
    return list({thread_id, normalized, f"<{normalized}>"})


def email_owner_filters(auth_context: AuthContext):
    organization_filter = (
        Email.organization_id == auth_context.organization_id
        if auth_context.organization_id is not None
        else Email.organization_id.is_(None)
    )
    return (Email.user_id == auth_context.user_id, organization_filter)


MailFolder = Literal["inbox", "sent"]


def thread_matches_folder(
    thread_messages: list[Email], user_addresses: set[str], folder: MailFolder
) -> bool:
    if folder == "sent":
        return any(
            message_is_from_user(email_message, user_addresses)
            for email_message in thread_messages
        )
    return True


def _to_dedupe_candidate(
    candidate: "UniqueThreadCandidateRequest",
) -> EmailDedupeCandidate:
    return EmailDedupeCandidate(
        candidate_key=candidate.candidate_key,
        message_id=candidate.message_id,
        sender=candidate.sender,
        recipients=candidate.recipients,
        subject=candidate.subject,
        date=candidate.date,
        body=candidate.body,
    )


def _email_message_lookup_values(email_row: Email) -> set[str]:
    normalized = normalize_message_id(email_row.message_id)
    if not normalized:
        return set()
    return {normalized, f"<{normalized}>"}


class EmailListItem(BaseModel):
    id: int
    thread_id: str | None = None
    subject: str | None
    sender: str
    reply_to: str | None = None
    date: datetime.datetime
    snippet: str
    reply_count: int | None = None
    has_draft: bool = False
    is_self_sent: bool = False
    requires_reply: bool = False
    schedule_conflict: bool = False


class EmailDetailResponse(BaseModel):
    id: int
    message_id: str
    thread_id: str | None = None
    sender: str
    reply_to: str | None = None
    recipients: str | None
    subject: str | None
    date: datetime.datetime
    body: str
    in_reply_to: str | None = None
    references: str | None = None
    requires_reply: bool = False
    schedule_conflict: bool = False


class UniqueThreadCandidateRequest(BaseModel):
    candidate_key: str = Field(min_length=1, max_length=128)
    message_id: str | None = Field(default=None, max_length=512)
    sender: str | None = Field(default=None, max_length=512)
    recipients: str | None = Field(default=None, max_length=2048)
    subject: str | None = Field(default=None, max_length=1024)
    date: datetime.datetime | None = None
    body: str | None = Field(default=None, max_length=20000)


class UniqueThreadIntentRequest(BaseModel):
    candidates: list[UniqueThreadCandidateRequest] = Field(
        min_length=1, max_length=20
    )


class UniqueThreadUpdate(BaseModel):
    candidate_key: str
    canonical_thread_id: str
    dedupe_key: str
    match_reason: Literal["message_id", "fingerprint"]
    existing_message_id: str


class UniqueThreadIntentResponse(BaseModel):
    status: Literal["intent_ready"]
    candidates_checked: int
    duplicates_found: int
    thread_updates: list[UniqueThreadUpdate]
    provenance: Literal["server-authoritative"]
    provider_write_executed: bool
    audit_event: Literal["email.unique_thread_intent.created"]


@router.get("", response_model=dict[str, list[EmailListItem]])
async def get_emails(
    limit: int = Query(default=50, ge=1, le=200),
    folder: MailFolder = Query(default="inbox"),
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    tenant_config = await get_scoped_tenant_config(
        db,
        auth_context.user_id,
        auth_context.organization_id,
    )
    user_addresses = configured_email_addresses(tenant_config)
    candidate_window = min(max(limit * 10, 200), 2000)
    result = await db.execute(
        select(Email)
        .where(*email_owner_filters(auth_context))
        .order_by(Email.date.desc())
        .limit(candidate_window)
    )
    emails = result.scalars().all()
    emails = sorted(emails, key=lambda item: item.date)

    grouped = {}
    reply_counts = {}
    thread_messages = {}
    for email in emails:
        group_key = canonical_thread_key(email)
        thread_messages.setdefault(group_key, []).append(email)
        if group_key not in grouped:
            grouped[group_key] = email
            reply_counts[group_key] = 1
        else:
            reply_counts[group_key] += 1
            if email.date > grouped[group_key].date:
                grouped[group_key] = email

    visible_groups = [
        email
        for group_key, email in grouped.items()
        if thread_matches_folder(thread_messages[group_key], user_addresses, folder)
    ]
    sorted_groups = sorted(visible_groups, key=lambda x: x.date, reverse=True)[:limit]

    items = []
    for email in sorted_groups:
        group_key = canonical_thread_key(email)
        snippet = email.body[:100] + "..." if len(email.body) > 100 else email.body
        items.append(
            EmailListItem(
                id=email.id,
                subject=email.subject,
                sender=email.sender,
                reply_to=email.reply_to,
                date=email.date,
                snippet=snippet,
                thread_id=group_key,
                reply_count=reply_counts[group_key],
                is_self_sent=message_is_self_sent(email, user_addresses),
                requires_reply=thread_requires_reply(
                    thread_messages[group_key], user_addresses
                ),
            )
        )
    return {"emails": items}


@router.get("/pending-replies", response_model=dict[str, list[EmailListItem]])
async def get_pending_replies(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    pending_emails = await check_missing_replies(
        db, auth_context.user_id, auth_context.organization_id
    )
    items = []
    for email in pending_emails[:limit]:
        snippet = email.body[:100] + "..." if len(email.body) > 100 else email.body
        items.append(
            EmailListItem(
                id=email.id,
                subject=email.subject,
                sender=email.sender,
                reply_to=email.reply_to,
                date=email.date,
                snippet=snippet,
                thread_id=canonical_thread_key(email),
                reply_count=None,
                is_self_sent=False,
                requires_reply=True,
            )
        )
    return {"emails": items}



def _extract_candidate_lookups(candidates: list[EmailDedupeCandidate]) -> tuple[set[str], set[str]]:
    message_lookup_values: set[str] = set()
    fingerprint_values: set[str] = set()
    for candidate in candidates:
        message_lookup_values.update(candidate_message_lookup_values(candidate))
        candidate_fingerprint = candidate_strong_fingerprint(candidate)
        if candidate_fingerprint:
            fingerprint_values.add(candidate_fingerprint)
    return message_lookup_values, fingerprint_values


async def _fetch_existing_emails_for_candidates(
    db: AsyncSession,
    auth_context: AuthContext,
    message_lookup_values: set[str],
    fingerprint_values: set[str],
) -> list[Email]:
    predicates = []
    if message_lookup_values:
        predicates.append(Email.message_id.in_(message_lookup_values))
    if fingerprint_values:
        predicates.append(Email.fingerprint.in_(fingerprint_values))

    if not predicates:
        return []

    result = await db.execute(
        select(Email).where(
            *email_owner_filters(auth_context),
            or_(*predicates),
        )
    )
    return list(result.scalars().all())


def _build_email_lookup_dicts(
    existing_emails: list[Email],
) -> tuple[dict[str, Email], dict[str, Email]]:
    by_message_id: dict[str, Email] = {}
    by_fingerprint: dict[str, Email] = {}
    for email_row in existing_emails:
        for lookup_value in _email_message_lookup_values(email_row):
            by_message_id.setdefault(lookup_value, email_row)
        row_fingerprint = email_strong_fingerprint(email_row)
        if row_fingerprint:
            by_fingerprint.setdefault(row_fingerprint, email_row)
        if email_row.fingerprint:
            by_fingerprint.setdefault(email_row.fingerprint, email_row)
    return by_message_id, by_fingerprint


def _find_matches_for_candidates(
    candidates: list[EmailDedupeCandidate],
    by_message_id: dict[str, Email],
    by_fingerprint: dict[str, Email],
) -> list[UniqueThreadUpdate]:
    updates: list[UniqueThreadUpdate] = []
    for candidate in candidates:
        matched_email: Email | None = None
        match_reason: Literal["message_id", "fingerprint"] | None = None
        dedupe_key: str | None = None

        for lookup_value in candidate_message_lookup_values(candidate):
            if lookup_value in by_message_id:
                matched_email = by_message_id[lookup_value]
                match_reason = "message_id"
                dedupe_key = normalize_message_id(lookup_value) or lookup_value
                break

        if matched_email is None:
            candidate_fingerprint = candidate_strong_fingerprint(candidate)
            if candidate_fingerprint and candidate_fingerprint in by_fingerprint:
                matched_email = by_fingerprint[candidate_fingerprint]
                match_reason = "fingerprint"
                dedupe_key = f"sha256:{candidate_fingerprint[:16]}"

        if matched_email is not None and match_reason and dedupe_key:
            updates.append(
                UniqueThreadUpdate(
                    candidate_key=candidate.candidate_key,
                    canonical_thread_id=canonical_thread_key(matched_email),
                    dedupe_key=dedupe_key,
                    match_reason=match_reason,
                    existing_message_id=(
                        normalize_message_id(matched_email.message_id)
                        or matched_email.message_id
                    ),
                )
            )
    return updates


@router.post("/unique-thread-intent", response_model=UniqueThreadIntentResponse)
async def create_unique_thread_intent(
    request: UniqueThreadIntentRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    candidates = [_to_dedupe_candidate(candidate) for candidate in request.candidates]
    message_lookup_values, fingerprint_values = _extract_candidate_lookups(candidates)
    existing_emails = await _fetch_existing_emails_for_candidates(
        db, auth_context, message_lookup_values, fingerprint_values
    )
    by_message_id, by_fingerprint = _build_email_lookup_dicts(existing_emails)
    updates = _find_matches_for_candidates(candidates, by_message_id, by_fingerprint)

    return UniqueThreadIntentResponse(
        status="intent_ready",
        candidates_checked=len(candidates),
        duplicates_found=len(updates),
        thread_updates=updates,
        provenance="server-authoritative",
        provider_write_executed=False,
        audit_event="email.unique_thread_intent.created",
    )


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(
    email_id: int,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    result = await db.execute(
        select(Email).where(Email.id == email_id, *email_owner_filters(auth_context))
    )
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return EmailDetailResponse(
        id=email.id,
        message_id=email.message_id,
        sender=email.sender,
        reply_to=email.reply_to,
        recipients=email.recipients,
        subject=email.subject,
        date=email.date,
        body=email.body,
        thread_id=canonical_thread_key(email),
        in_reply_to=email.in_reply_to,
        references=email.references,
    )


@router.get(
    "/thread/{thread_id:path}", response_model=dict[str, list[EmailDetailResponse]]
)
async def get_email_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    lookup_values = thread_lookup_values(thread_id)
    result = await db.execute(
        select(Email)
        .where(
            *email_owner_filters(auth_context),
            or_(
                Email.thread_id.in_(lookup_values), Email.message_id.in_(lookup_values)
            ),
        )
        .order_by(Email.date.asc())
    )
    emails = result.scalars().all()
    emails = sorted(emails, key=lambda item: item.date)
    if not emails:
        raise HTTPException(status_code=404, detail="Thread not found")

    items = []
    for email in emails:
        items.append(
            EmailDetailResponse(
                id=email.id,
                message_id=email.message_id,
                sender=email.sender,
                reply_to=email.reply_to,
                recipients=email.recipients,
                subject=email.subject,
                date=email.date,
                body=email.body,
                thread_id=canonical_thread_key(email),
                in_reply_to=email.in_reply_to,
                references=email.references,
            )
        )
    return {"thread": items}


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    in_reply_to: str | None = None  # O3: email threading support
    references: str | None = None


@router.post("/send")
async def send_email_endpoint(
    request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    try:
        tenant_config = await get_scoped_tenant_config(
            db,
            auth_context.user_id,
            auth_context.organization_id,
        )

        if (
            not tenant_config
            or not tenant_config.smtp_server
            or not tenant_config.smtp_port
            or not tenant_config.smtp_username
        ):
            raise HTTPException(status_code=400, detail="SMTP is not configured")

        try:
            smtp_server = tenant_config.smtp_server
            smtp_port = tenant_config.smtp_port
            smtp_username = tenant_config.smtp_username
            smtp_password = tenant_config.smtp_password
            validate_smtp_destination(smtp_server, smtp_port)
        except Exception as exc:
            if "ENCRYPTION_KEY is required" in str(exc):
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Server encryption key is not configured. "
                        "Contact your workspace administrator."
                    ),
                ) from exc
            if isinstance(exc, ValueError):
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            raise

        message_params = EmailMessageParams(
            to_address=request.to,
            subject=request.subject,
            body=request.body,
            in_reply_to=request.in_reply_to,
            references=request.references,
        )
        smtp_config = SmtpConfig(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
        )
        send_result = await send_email(
            message_params=message_params,
            smtp_config=smtp_config,
        )
        if send_result.get("status") not in {"sent", "simulated"}:
            raise HTTPException(status_code=500, detail="Failed to send email")
        return send_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal error occurred while sending the email"
        )
