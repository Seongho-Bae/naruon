import datetime
import hashlib
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from sqlalchemy import bindparam, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Attachment, Email
from services.archive import extract_backup_async
from services.email_dedupe_service import strong_email_fingerprint
from services.email_parser import EmailData, parse_eml_bytes
from services.exceptions import ArchiveError, EmailParseError
from services.threading_service import (
    assign_thread_id,
    email_owner_filters,
    generate_email_fingerprint,
    normalize_message_id,
)

EMBEDDING_DIMENSION = 1536
MAX_IMPORT_UPLOADS = 10
MAX_IMPORT_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMPORT_EML_FILES = 100
MAX_IMPORT_EMAILS_PER_OWNER = 1000
EMAIL_IMPORT_QUOTA_LOCK_NAMESPACE = "naruon-email-import-quota"

EmailImportItemStatus = Literal["imported", "skipped_duplicate", "failed"]


class EmailImportQuotaExceeded(Exception):
    pass


@dataclass(frozen=True)
class EmailImportUpload:
    filename: str
    content: bytes


@dataclass
class EmailImportItemResult:
    filename: str
    status: EmailImportItemStatus
    reason_code: str | None = None
    attachment_count: int = 0


@dataclass
class EmailImportResult:
    imported_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    attachment_count: int = 0
    items: list[EmailImportItemResult] = field(default_factory=list)

    def add_item(self, item: EmailImportItemResult) -> None:
        self.items.append(item)
        if item.status == "imported":
            self.imported_count += 1
            self.attachment_count += item.attachment_count
        elif item.status == "skipped_duplicate":
            self.skipped_count += 1
        else:
            self.failed_count += 1


def _safe_upload_filename(filename: str) -> str:
    name = Path(filename or "upload").name.strip()
    return name or "upload"


def _safe_item_filename(upload_name: str, eml_path: Path | None = None) -> str:
    safe_upload_name = _safe_upload_filename(upload_name)
    if eml_path is None or eml_path.name == safe_upload_name:
        return safe_upload_name
    return f"{safe_upload_name}:{eml_path.name}"


def _utc_datetime(value: object) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)
    return datetime.datetime.now(datetime.timezone.utc)


def _fallback_message_id(content: bytes) -> str:
    digest = hashlib.sha256(content).hexdigest()
    return f"import-{digest}@local.naruon"


def _message_id_for(parsed: EmailData, content: bytes) -> str:
    return normalize_message_id(parsed.get("message_id")) or _fallback_message_id(
        content
    )


def _email_fingerprint(parsed: EmailData, persisted_date: datetime.datetime) -> str:
    strong_fingerprint = strong_email_fingerprint(
        sender=parsed.get("sender"),
        subject=parsed.get("subject"),
        date=persisted_date,
        body=parsed.get("body"),
    )
    if strong_fingerprint:
        return strong_fingerprint
    return generate_email_fingerprint(
        parsed.get("subject"),
        persisted_date.isoformat(),
        parsed.get("sender"),
        parsed.get("recipients"),
    )


async def _find_existing_email(
    session: AsyncSession,
    *,
    user_id: str,
    organization_id: str,
    message_id: str,
    fingerprint: str,
) -> Email | None:
    message_lookup_values = {message_id, f"<{message_id}>"}
    result = await session.execute(
        select(Email).where(
            *email_owner_filters(user_id, organization_id),
            or_(
                Email.message_id.in_(message_lookup_values),
                Email.fingerprint == fingerprint,
            ),
        )
    )
    return result.scalar_one_or_none()


async def _owner_email_import_count(
    session: AsyncSession, *, user_id: str, organization_id: str
) -> int:
    count = await session.scalar(
        select(func.count(Email.id)).where(
            *email_owner_filters(user_id, organization_id)
        )
    )
    return int(count or 0)


def _session_uses_postgresql(session: AsyncSession) -> bool:
    try:
        bind = session.get_bind()
    except Exception:
        return False
    return getattr(getattr(bind, "dialect", None), "name", None) == "postgresql"


async def _acquire_owner_import_quota_lock(
    session: AsyncSession, *, user_id: str, organization_id: str
) -> bool:
    if not _session_uses_postgresql(session):
        return False
    lock_params = {
        "namespace_key": EMAIL_IMPORT_QUOTA_LOCK_NAMESPACE,
        "owner_key": f"{user_id}\x00{organization_id}",
    }
    await session.execute(
        select(
            func.pg_advisory_lock(
                func.hashtext(bindparam("namespace_key")),
                func.hashtext(bindparam("owner_key")),
            )
        ),
        lock_params,
    )
    return True


async def _release_owner_import_quota_lock(
    session: AsyncSession, *, user_id: str, organization_id: str
) -> None:
    lock_params = {
        "namespace_key": EMAIL_IMPORT_QUOTA_LOCK_NAMESPACE,
        "owner_key": f"{user_id}\x00{organization_id}",
    }
    await session.execute(
        select(
            func.pg_advisory_unlock(
                func.hashtext(bindparam("namespace_key")),
                func.hashtext(bindparam("owner_key")),
            )
        ),
        lock_params,
    )


async def _import_single_eml(
    session: AsyncSession,
    *,
    eml_path: Path,
    display_filename: str,
    user_id: str,
    organization_id: str,
) -> EmailImportItemResult:
    try:
        content = _read_eml_bytes(eml_path)
        parsed = parse_eml_bytes(content)
    except EmailParseError:
        return EmailImportItemResult(
            filename=display_filename,
            status="failed",
            reason_code="parse_failed",
        )

    message_id = _message_id_for(parsed, content)
    parsed["message_id"] = message_id
    persisted_date = _utc_datetime(parsed.get("date"))
    fingerprint = _email_fingerprint(parsed, persisted_date)

    existing_email = await _find_existing_email(
        session,
        user_id=user_id,
        organization_id=organization_id,
        message_id=message_id,
        fingerprint=fingerprint,
    )
    if existing_email is not None:
        return EmailImportItemResult(
            filename=display_filename,
            status="skipped_duplicate",
            reason_code="duplicate_email",
        )

    thread_id = await assign_thread_id(
        session,
        parsed,
        user_id=user_id,
        organization_id=organization_id,
    )
    email_obj = Email(
        user_id=user_id,
        organization_id=organization_id,
        message_id=message_id,
        thread_id=thread_id,
        fingerprint=fingerprint,
        sender=parsed.get("sender", ""),
        reply_to=parsed.get("reply_to"),
        recipients=parsed.get("recipients"),
        subject=parsed.get("subject"),
        in_reply_to=parsed.get("in_reply_to"),
        references=parsed.get("references"),
        date=persisted_date,
        body=parsed.get("body", ""),
        embedding=[0.0] * EMBEDDING_DIMENSION,
    )

    attachment_count = 0
    for attachment in parsed.get("attachments", []):
        email_obj.attachments.append(
            Attachment(
                filename=str(attachment.get("filename") or "attachment.txt"),
                content=str(attachment.get("content") or ""),
                embedding=[0.0] * EMBEDDING_DIMENSION,
            )
        )
        attachment_count += 1

    session.add(email_obj)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        return EmailImportItemResult(
            filename=display_filename,
            status="failed",
            reason_code="database_commit_failed",
        )

    return EmailImportItemResult(
        filename=display_filename,
        status="imported",
        attachment_count=attachment_count,
    )


def _read_eml_bytes(eml_path: Path) -> bytes:
    no_follow_flag = getattr(os, "O_NOFOLLOW", None)
    if no_follow_flag is None:
        raise EmailParseError(
            f"Failed to read file {eml_path}: symlink-safe file operations not supported on this platform"
        )

    open_flags = os.O_RDONLY | no_follow_flag
    try:
        file_descriptor = os.open(eml_path, open_flags)
    except OSError as exc:
        raise EmailParseError(f"Failed to read file {eml_path}: {exc}") from exc

    try:
        file_stat = os.fstat(file_descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise EmailParseError(f"Failed to read file {eml_path}: not a regular file")
        file_handle = os.fdopen(file_descriptor, "rb")
        file_descriptor = -1
        with file_handle:
            return file_handle.read()
    except OSError as exc:
        raise EmailParseError(f"Failed to read file {eml_path}: {exc}") from exc
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)


def _is_regular_eml_path(path: Path) -> bool:
    if path.suffix.lower() != ".eml":
        return False
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False


async def _eml_paths_for_upload(
    *,
    upload: EmailImportUpload,
    upload_dir: Path,
) -> tuple[list[Path], str | None]:
    upload_name = _safe_upload_filename(upload.filename)
    upload_path = upload_dir / upload_name
    upload_path.write_bytes(upload.content)

    suffix = upload_path.suffix.lower()
    if suffix == ".eml":
        return [upload_path], None
    if suffix != ".zip":
        return [], "unsupported_file_type"

    extract_dir = upload_dir / "extracted"
    try:
        extracted_paths = await extract_backup_async(upload_path, extract_dir)
    except ArchiveError:
        return [], "archive_extract_failed"

    eml_paths = [path for path in extracted_paths if _is_regular_eml_path(path)]
    if not eml_paths:
        return [], "archive_contains_no_eml"
    if len(eml_paths) > MAX_IMPORT_EML_FILES:
        return [], "archive_too_many_eml_files"
    return eml_paths, None


async def import_email_uploads(
    session: AsyncSession,
    *,
    uploads: list[EmailImportUpload],
    user_id: str,
    organization_id: str,
) -> EmailImportResult:
    lock_acquired = await _acquire_owner_import_quota_lock(
        session, user_id=user_id, organization_id=organization_id
    )
    try:
        result = EmailImportResult()
        existing_email_count = await _owner_email_import_count(
            session, user_id=user_id, organization_id=organization_id
        )
        remaining_quota = MAX_IMPORT_EMAILS_PER_OWNER - existing_email_count
        if remaining_quota <= 0:
            raise EmailImportQuotaExceeded()

        with TemporaryDirectory(prefix="naruon-email-import-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            planned_imports: list[tuple[str, Path]] = []
            for index, upload in enumerate(uploads):
                upload_name = _safe_upload_filename(upload.filename)
                upload_dir = temp_dir / f"upload_{index}"
                upload_dir.mkdir(parents=True, exist_ok=True)
                eml_paths, failure_reason = await _eml_paths_for_upload(
                    upload=upload,
                    upload_dir=upload_dir,
                )
                if failure_reason is not None:
                    result.add_item(
                        EmailImportItemResult(
                            filename=upload_name,
                            status="failed",
                            reason_code=failure_reason,
                        )
                    )
                    continue

                planned_imports.extend(
                    (
                        _safe_item_filename(upload_name, eml_path),
                        eml_path,
                    )
                    for eml_path in eml_paths
                )

            if len(planned_imports) > remaining_quota:
                raise EmailImportQuotaExceeded()

            for display_filename, eml_path in planned_imports:
                result.add_item(
                    await _import_single_eml(
                        session,
                        eml_path=eml_path,
                        display_filename=display_filename,
                        user_id=user_id,
                        organization_id=organization_id,
                    )
                )
    finally:
        if lock_acquired:
            await _release_owner_import_quota_lock(
                session, user_id=user_id, organization_id=organization_id
            )

    return result
