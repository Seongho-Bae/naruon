import datetime
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Attachment, Email
from services.archive import extract_backup_async
from services.email_dedupe_service import strong_email_fingerprint
from services.email_parser import EmailData, parse_eml
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

EmailImportItemStatus = Literal["imported", "skipped_duplicate", "failed"]


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
    return normalize_message_id(parsed.get("message_id")) or _fallback_message_id(content)


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


async def _import_single_eml(
    session: AsyncSession,
    *,
    eml_path: Path,
    display_filename: str,
    user_id: str,
    organization_id: str,
) -> EmailImportItemResult:
    content = eml_path.read_bytes()
    try:
        parsed = parse_eml(eml_path)
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

    eml_paths = [
        path
        for path in extracted_paths
        if path.is_file() and path.suffix.lower() == ".eml"
    ]
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
    result = EmailImportResult()

    with TemporaryDirectory(prefix="naruon-email-import-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
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

            for eml_path in eml_paths:
                result.add_item(
                    await _import_single_eml(
                        session,
                        eml_path=eml_path,
                        display_filename=_safe_item_filename(upload_name, eml_path),
                        user_id=user_id,
                        organization_id=organization_id,
                    )
                )

    return result
