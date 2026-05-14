from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.models import MailboxAccount
from db.session import get_db
from services.email_parser import _sanitize_nul
from services.mail_server_security import (
    MailServerValidationError,
    validate_mail_server_host,
)

router = APIRouter(prefix="/api/mailbox-accounts")

SECRET_FIELDS = {"smtp_password", "imap_password", "pop3_password"}


class MailboxAccountCreate(BaseModel):
    email_address: str
    display_name: str | None = None
    provider: str = "custom"
    is_default_reply: bool = False
    is_active: bool = True
    smtp_server: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    imap_server: str | None = None
    imap_port: int | None = None
    imap_username: str | None = None
    imap_password: str | None = None
    pop3_server: str | None = None
    pop3_port: int | None = None
    pop3_username: str | None = None
    pop3_password: str | None = None


class MailboxAccountUpdate(BaseModel):
    email_address: str | None = None
    display_name: str | None = None
    provider: str | None = None
    is_default_reply: bool | None = None
    is_active: bool | None = None
    smtp_server: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    imap_server: str | None = None
    imap_port: int | None = None
    imap_username: str | None = None
    imap_password: str | None = None
    pop3_server: str | None = None
    pop3_port: int | None = None
    pop3_username: str | None = None
    pop3_password: str | None = None


class MailboxAccountResponse(BaseModel):
    id: int
    user_id: str
    email_address: str
    display_name: str | None = None
    provider: str
    is_default_reply: bool
    is_active: bool
    smtp_server: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password_set: bool
    imap_server: str | None = None
    imap_port: int | None = None
    imap_username: str | None = None
    imap_password_set: bool
    pop3_server: str | None = None
    pop3_port: int | None = None
    pop3_username: str | None = None
    pop3_password_set: bool

    model_config = ConfigDict(from_attributes=True)


class MailboxAccountListResponse(BaseModel):
    items: list[MailboxAccountResponse]


def _sanitize_mailbox_payload(payload: dict[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            normalized = _sanitize_nul(value)
            if key in {
                "email_address",
                "provider",
                "smtp_server",
                "smtp_username",
                "imap_server",
                "imap_username",
                "pop3_server",
                "pop3_username",
            }:
                normalized = normalized.strip()
            if key == "display_name":
                normalized = normalized.strip()
            sanitized[key] = normalized
        else:
            sanitized[key] = value
    return sanitized


def _validate_mailbox_payload(payload: dict[str, object]) -> dict[str, object]:
    email_address = payload.get("email_address")
    if isinstance(email_address, str) and not email_address:
        raise HTTPException(
            status_code=400, detail="메일 주소는 비어 있을 수 없습니다."
        )

    for prefix, label in (("smtp", "SMTP"), ("imap", "IMAP"), ("pop3", "POP3")):
        server = payload.get(f"{prefix}_server")
        port = payload.get(f"{prefix}_port")
        has_server = isinstance(server, str) and bool(server)
        has_port = port is not None
        if has_server != has_port:
            raise HTTPException(
                status_code=400, detail=f"{label} 서버와 포트는 함께 설정해야 합니다."
            )
        if has_server and isinstance(server, str) and isinstance(port, int):
            try:
                payload[f"{prefix}_server"] = validate_mail_server_host(
                    prefix,
                    label,
                    server,
                    port,
                )
            except MailServerValidationError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

    if payload.get("is_default_reply") is True:
        payload["is_active"] = True
    return payload


def _serialize_account(account: MailboxAccount) -> MailboxAccountResponse:
    return MailboxAccountResponse(
        id=account.id,
        user_id=account.user_id,
        email_address=account.email_address,
        display_name=account.display_name,
        provider=account.provider,
        is_default_reply=account.is_default_reply,
        is_active=account.is_active,
        smtp_server=account.smtp_server,
        smtp_port=account.smtp_port,
        smtp_username=account.smtp_username,
        smtp_password_set=bool(account.smtp_password),
        imap_server=account.imap_server,
        imap_port=account.imap_port,
        imap_username=account.imap_username,
        imap_password_set=bool(account.imap_password),
        pop3_server=account.pop3_server,
        pop3_port=account.pop3_port,
        pop3_username=account.pop3_username,
        pop3_password_set=bool(account.pop3_password),
    )


async def _get_account_or_404(
    db: AsyncSession, current_user: str, account_id: int
) -> MailboxAccount:
    result = await db.execute(
        select(MailboxAccount).where(
            MailboxAccount.id == account_id, MailboxAccount.user_id == current_user
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Mailbox account not found")
    return account


async def _clear_default_reply(db: AsyncSession, current_user: str) -> None:
    result = await db.execute(
        select(MailboxAccount).where(MailboxAccount.user_id == current_user)
    )
    for account in result.scalars().all():
        account.is_default_reply = False


@router.get("", response_model=MailboxAccountListResponse)
async def list_mailbox_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(MailboxAccount).where(MailboxAccount.user_id == current_user)
    )
    accounts = sorted(
        result.scalars().all(), key=lambda item: item.updated_at, reverse=True
    )
    return {"items": [_serialize_account(account) for account in accounts]}


@router.post("")
async def create_mailbox_account(
    payload: MailboxAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    if payload.is_default_reply:
        await _clear_default_reply(db, current_user)

    account_payload = _validate_mailbox_payload(
        _sanitize_mailbox_payload(payload.model_dump())
    )
    account = MailboxAccount(user_id=current_user, **account_payload)
    db.add(account)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Mailbox account already exists")
    except Exception as exc:
        await db.rollback()
        if "ENCRYPTION_KEY is required" not in str(exc):
            raise
        raise HTTPException(
            status_code=503,
            detail="Server encryption key is not configured. Contact your workspace administrator.",
        ) from exc
    await db.refresh(account)
    return {"item": _serialize_account(account)}


@router.patch("/{account_id}")
async def update_mailbox_account(
    account_id: int,
    payload: MailboxAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    account = await _get_account_or_404(db, current_user, account_id)
    update_data = _validate_mailbox_payload(
        _sanitize_mailbox_payload(payload.model_dump(exclude_unset=True))
    )
    if update_data.get("is_default_reply"):
        await _clear_default_reply(db, current_user)
    for key, value in update_data.items():
        if key in SECRET_FIELDS and value == "********":
            continue
        setattr(account, key, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Mailbox account already exists")
    except Exception as exc:
        await db.rollback()
        if "ENCRYPTION_KEY is required" not in str(exc):
            raise
        raise HTTPException(
            status_code=503,
            detail="Server encryption key is not configured. Contact your workspace administrator.",
        ) from exc
    await db.refresh(account)
    return {"item": _serialize_account(account)}


@router.post("/{account_id}/make-default-reply")
async def make_default_reply(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    account = await _get_account_or_404(db, current_user, account_id)
    await _clear_default_reply(db, current_user)
    account.is_default_reply = True
    account.is_active = True
    await db.commit()
    await db.refresh(account)
    return {"item": _serialize_account(account)}
