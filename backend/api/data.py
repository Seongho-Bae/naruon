from datetime import datetime, timezone
import hashlib
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import AuthContext, get_auth_context, is_admin_role
from core.config import settings
from db.models import (
    Attachment,
    ConnectorSignalEvent,
    Email,
    ProjectFolder,
    WebdavAccount,
)
from db.session import get_db

router = APIRouter(prefix="/api/data", tags=["data"])

DATA_VECTOR_DIMENSIONS = 1536
SurfaceStatus = Literal[
    "ready",
    "running",
    "needs_attention",
    "pending",
    "no_source",
]
QualityStatus = Literal["pass", "needs_attention", "pending"]
RepositoryAssetState = Literal["ready", "needs_attention"]
RepositoryType = Literal[
    "webdav_account",
    "project_folder",
    "email_repository",
    "attachment_repository",
]


class DataRepositorySummary(BaseModel):
    source_id: str
    repository_type: RepositoryType
    display_name: str
    object_count: int
    writeback_enabled: bool | None
    evidence_source: str
    provider_write_executed: bool


class DataRepositoryAsset(BaseModel):
    asset_key: str
    asset_type: Literal["email_attachment"]
    display_name: str
    source_label: str
    state_code: RepositoryAssetState
    detail_text: str
    content_chars: int
    captured_at: str
    evidence_source: str
    thread_key: str
    provider_write_executed: bool


class DataPipelineStage(BaseModel):
    stage_key: str
    display_name: str
    status_code: SurfaceStatus
    progress_percent: int
    evidence_source: str
    detail_text: str
    provider_write_executed: bool


class DataEmbeddingCollection(BaseModel):
    collection_key: str
    display_name: str
    object_count: int
    embedded_count: int
    embedding_model: str
    vector_dimensions: int
    status_code: SurfaceStatus
    evidence_source: str
    provider_write_executed: bool


class DataQualityCheck(BaseModel):
    check_key: str
    display_name: str
    status_code: QualityStatus
    issue_count: int
    total_count: int
    evidence_source: str
    detail_text: str
    provider_write_executed: bool


class DataConnectorEvent(BaseModel):
    event_uid: str
    signal_key: str
    state_code: str
    detail_text: str | None
    observed_at: str


class DataQualitySurfaceResponse(BaseModel):
    workspace_id: str
    organization_id: str | None
    audit_event: Literal["data.quality_surface.viewed"]
    provider_write_executed: bool
    repositories: list[DataRepositorySummary]
    repository_assets: list[DataRepositoryAsset]
    pipeline_stages: list[DataPipelineStage]
    embedding_collections: list[DataEmbeddingCollection]
    quality_checks: list[DataQualityCheck]
    connector_events: list[DataConnectorEvent]


def _datetime_to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_display_text(value: str | None, fallback: str) -> str:
    cleaned = (value or fallback).replace("<", "").replace(">", "").strip()
    return " ".join(cleaned.split())[:120] or fallback


def _opaque_asset_key(email: Email, attachment: Attachment) -> str:
    digest = hashlib.sha256(
        "|".join(
            [
                email.user_id,
                email.organization_id,
                email.message_id,
                attachment.filename,
            ]
        ).encode("utf-8")
    ).hexdigest()
    return f"asset_{digest[:24]}"


def _opaque_thread_key(email: Email) -> str:
    if not email.thread_id:
        return "thread_missing"
    digest = hashlib.sha256(email.thread_id.encode("utf-8")).hexdigest()
    return f"thread_{digest[:16]}"


def _can_read_org_scope(auth_context: AuthContext) -> bool:
    return is_admin_role(auth_context.role) and auth_context.organization_id is not None


def _owner_scope_statement(model, auth_context: AuthContext):
    statement = select(model)
    if hasattr(model, "workspace_id"):
        statement = statement.where(model.workspace_id == auth_context.workspace_id)
    if _can_read_org_scope(auth_context):
        return statement.where(model.organization_id == auth_context.organization_id)
    organization_filter = (
        model.organization_id == auth_context.organization_id
        if auth_context.organization_id is not None
        else model.organization_id.is_(None)
    )
    return statement.where(model.user_id == auth_context.user_id, organization_filter)


def _email_scope_filter(auth_context: AuthContext):
    if _can_read_org_scope(auth_context):
        organization_filter = Email.organization_id == auth_context.organization_id
        return (organization_filter, organization_filter)
    organization_filter = (
        Email.organization_id == auth_context.organization_id
        if auth_context.organization_id is not None
        else Email.organization_id.is_(None)
    )
    return (Email.user_id == auth_context.user_id, organization_filter)


def _connector_scope_statement(auth_context: AuthContext):
    if auth_context.organization_id is None:
        return None
    return (
        select(ConnectorSignalEvent)
        .where(
            ConnectorSignalEvent.organization_id == auth_context.organization_id,
            ConnectorSignalEvent.workspace_id == auth_context.workspace_id,
        )
        .order_by(ConnectorSignalEvent.observed_at.desc())
        .limit(8)
    )


async def _scoped_rows(db: AsyncSession, statement):
    result = await db.execute(statement)
    return list(result.scalars().all())


async def _count_scalar(db: AsyncSession, statement) -> int:
    result = await db.execute(statement)
    return int(result.scalar_one() or 0)


def _status_from_ratio(total_count: int, ready_count: int) -> SurfaceStatus:
    if total_count <= 0:
        return "pending"
    if ready_count <= 0:
        return "needs_attention"
    if ready_count < total_count:
        return "running"
    return "ready"


def _progress_percent(total_count: int, ready_count: int) -> int:
    if total_count <= 0:
        return 0
    return max(0, min(100, round((ready_count / total_count) * 100)))


def _quality_status(total_count: int, issue_count: int) -> QualityStatus:
    if total_count <= 0:
        return "pending"
    return "pass" if issue_count == 0 else "needs_attention"


def _quality_detail(
    *,
    total_count: int,
    issue_count: int,
    ready_text: str,
    empty_text: str,
    issue_text: str,
) -> str:
    if total_count <= 0:
        return empty_text
    if issue_count == 0:
        return ready_text
    return issue_text


def _repository_summaries(
    webdav_accounts: list[WebdavAccount],
    project_folders: list[ProjectFolder],
    email_count: int,
    attachment_count: int,
) -> list[DataRepositorySummary]:
    repositories: list[DataRepositorySummary] = [
        DataRepositorySummary(
            source_id="email_repository",
            repository_type="email_repository",
            display_name="Scoped email archive",
            object_count=email_count,
            writeback_enabled=None,
            evidence_source="emails",
            provider_write_executed=False,
        ),
        DataRepositorySummary(
            source_id="attachment_repository",
            repository_type="attachment_repository",
            display_name="Scoped attachment archive",
            object_count=attachment_count,
            writeback_enabled=None,
            evidence_source="attachments",
            provider_write_executed=False,
        ),
    ]
    repositories.extend(
        DataRepositorySummary(
            source_id=account.source_uid,
            repository_type="webdav_account",
            display_name="Customer WebDAV account",
            object_count=0,
            writeback_enabled=bool(account.writeback_enabled),
            evidence_source="webdav_accounts",
            provider_write_executed=False,
        )
        for account in webdav_accounts
    )
    repositories.extend(
        DataRepositorySummary(
            source_id=folder.folder_uid,
            repository_type="project_folder",
            display_name=folder.project_name,
            object_count=0,
            writeback_enabled=None,
            evidence_source="project_folders",
            provider_write_executed=False,
        )
        for folder in project_folders
    )
    return repositories


def _repository_assets(rows) -> list[DataRepositoryAsset]:
    assets: list[DataRepositoryAsset] = []
    for attachment, email in rows:
        content_chars = len((attachment.content or "").strip())
        has_thread = bool((email.thread_id or "").strip())
        state_code: RepositoryAssetState = (
            "ready" if content_chars > 0 and has_thread else "needs_attention"
        )
        detail_parts: list[str] = []
        if content_chars <= 0:
            detail_parts.append("content extraction pending")
        if not has_thread:
            detail_parts.append("canonical thread pending")
        if not detail_parts:
            detail_parts.append("content and thread evidence ready")
        assets.append(
            DataRepositoryAsset(
                asset_key=_opaque_asset_key(email, attachment),
                asset_type="email_attachment",
                display_name=_safe_display_text(
                    attachment.filename, "email attachment"
                ),
                source_label=_safe_display_text(email.subject, "untitled email"),
                state_code=state_code,
                detail_text=", ".join(detail_parts),
                content_chars=content_chars,
                captured_at=_datetime_to_utc_iso(email.date),
                evidence_source="attachments.content, emails.thread_id",
                thread_key=_opaque_thread_key(email),
                provider_write_executed=False,
            )
        )
    return assets


def _pipeline_stages(
    *,
    source_count: int,
    email_count: int,
    attachment_count: int,
    missing_thread_count: int,
    embedded_total: int,
    object_total: int,
    connector_event_count: int,
) -> list[DataPipelineStage]:
    thread_ready = max(0, email_count - missing_thread_count)
    return [
        DataPipelineStage(
            stage_key="source_registry",
            display_name="Source registry",
            status_code="ready" if source_count > 0 else "no_source",
            progress_percent=100 if source_count > 0 else 0,
            evidence_source="webdav_accounts, project_folders",
            detail_text=f"{source_count} customer-owned sources are in scope.",
            provider_write_executed=False,
        ),
        DataPipelineStage(
            stage_key="ingestion_inventory",
            display_name="Ingestion inventory",
            status_code="ready" if email_count + attachment_count > 0 else "no_source",
            progress_percent=100 if email_count + attachment_count > 0 else 0,
            evidence_source="emails, attachments",
            detail_text=(
                f"{email_count} emails and {attachment_count} attachments "
                "are visible in the signed workspace scope."
            ),
            provider_write_executed=False,
        ),
        DataPipelineStage(
            stage_key="canonical_threading",
            display_name="Canonical threading",
            status_code=_status_from_ratio(email_count, thread_ready),
            progress_percent=_progress_percent(email_count, thread_ready),
            evidence_source="emails.thread_id",
            detail_text=f"{missing_thread_count} emails need canonical thread ids.",
            provider_write_executed=False,
        ),
        DataPipelineStage(
            stage_key="embedding_inventory",
            display_name="Embedding inventory",
            status_code=_status_from_ratio(object_total, embedded_total),
            progress_percent=_progress_percent(object_total, embedded_total),
            evidence_source="emails.embedding, attachments.embedding",
            detail_text=f"{embedded_total} of {object_total} objects have vectors.",
            provider_write_executed=False,
        ),
        DataPipelineStage(
            stage_key="connector_observability",
            display_name="Connector observability",
            status_code="ready" if connector_event_count > 0 else "pending",
            progress_percent=100 if connector_event_count > 0 else 0,
            evidence_source="connector_signal_events",
            detail_text=f"{connector_event_count} connector events are in scope.",
            provider_write_executed=False,
        ),
    ]


def _embedding_collections(
    *,
    email_count: int,
    embedded_email_count: int,
    attachment_count: int,
    embedded_attachment_count: int,
) -> list[DataEmbeddingCollection]:
    model_name = settings.OPENAI_EMBEDDING_MODEL
    return [
        DataEmbeddingCollection(
            collection_key="emails_embedding",
            display_name="Email vectors",
            object_count=email_count,
            embedded_count=embedded_email_count,
            embedding_model=model_name,
            vector_dimensions=DATA_VECTOR_DIMENSIONS,
            status_code=_status_from_ratio(email_count, embedded_email_count),
            evidence_source="emails.embedding",
            provider_write_executed=False,
        ),
        DataEmbeddingCollection(
            collection_key="attachments_embedding",
            display_name="Attachment vectors",
            object_count=attachment_count,
            embedded_count=embedded_attachment_count,
            embedding_model=model_name,
            vector_dimensions=DATA_VECTOR_DIMENSIONS,
            status_code=_status_from_ratio(
                attachment_count,
                embedded_attachment_count,
            ),
            evidence_source="attachments.embedding",
            provider_write_executed=False,
        ),
    ]


def _quality_checks(
    *,
    email_count: int,
    attachment_count: int,
    missing_thread_count: int,
    missing_fingerprint_count: int,
    blank_attachment_count: int,
    source_count: int,
    connector_event_count: int,
) -> list[DataQualityCheck]:
    return [
        DataQualityCheck(
            check_key="thread_id_integrity",
            display_name="Thread id integrity",
            status_code=_quality_status(email_count, missing_thread_count),
            issue_count=missing_thread_count,
            total_count=email_count,
            evidence_source="emails.thread_id",
            detail_text=_quality_detail(
                total_count=email_count,
                issue_count=missing_thread_count,
                ready_text="All scoped emails have canonical thread ids.",
                empty_text="No scoped emails are available yet.",
                issue_text="Some scoped emails need canonical thread ids.",
            ),
            provider_write_executed=False,
        ),
        DataQualityCheck(
            check_key="dedupe_fingerprint",
            display_name="Dedupe fingerprint",
            status_code=_quality_status(email_count, missing_fingerprint_count),
            issue_count=missing_fingerprint_count,
            total_count=email_count,
            evidence_source="emails.fingerprint",
            detail_text=_quality_detail(
                total_count=email_count,
                issue_count=missing_fingerprint_count,
                ready_text="All scoped emails have duplicate-detection fingerprints.",
                empty_text="No scoped emails are available yet.",
                issue_text="Some scoped emails need duplicate-detection fingerprints.",
            ),
            provider_write_executed=False,
        ),
        DataQualityCheck(
            check_key="attachment_content",
            display_name="Attachment content",
            status_code=_quality_status(attachment_count, blank_attachment_count),
            issue_count=blank_attachment_count,
            total_count=attachment_count,
            evidence_source="attachments.content",
            detail_text=_quality_detail(
                total_count=attachment_count,
                issue_count=blank_attachment_count,
                ready_text="All scoped attachments have extracted content.",
                empty_text="No scoped attachments are available yet.",
                issue_text="Some scoped attachments need extracted content.",
            ),
            provider_write_executed=False,
        ),
        DataQualityCheck(
            check_key="source_registry",
            display_name="Source registry coverage",
            status_code="pass" if source_count > 0 else "pending",
            issue_count=0 if source_count > 0 else 1,
            total_count=max(1, source_count),
            evidence_source="webdav_accounts, project_folders",
            detail_text=(
                "Customer-owned repositories are visible."
                if source_count > 0
                else "No customer-owned repositories are visible yet."
            ),
            provider_write_executed=False,
        ),
        DataQualityCheck(
            check_key="connector_signal",
            display_name="Connector signal coverage",
            status_code="pass" if connector_event_count > 0 else "pending",
            issue_count=0 if connector_event_count > 0 else 1,
            total_count=max(1, connector_event_count),
            evidence_source="connector_signal_events",
            detail_text=(
                "Connector evidence is visible for this workspace."
                if connector_event_count > 0
                else "Connector jobs have not emitted workspace evidence yet."
            ),
            provider_write_executed=False,
        ),
    ]


async def _fetch_repositories(
    db: AsyncSession, auth_context: AuthContext
) -> tuple[list[WebdavAccount], list[ProjectFolder]]:
    webdav_accounts = await _scoped_rows(
        db,
        _owner_scope_statement(WebdavAccount, auth_context).order_by(
            WebdavAccount.created_at.asc(),
            WebdavAccount.source_uid.asc(),
        ),
    )
    project_folders = await _scoped_rows(
        db,
        _owner_scope_statement(ProjectFolder, auth_context).order_by(
            ProjectFolder.created_at.asc(),
            ProjectFolder.folder_uid.asc(),
        ),
    )
    return webdav_accounts, project_folders


async def _fetch_object_counts(db: AsyncSession, email_scope: list) -> tuple[int, int]:
    email_count = await _count_scalar(
        db,
        select(func.count(Email.id)).where(*email_scope),
    )
    attachment_count = await _count_scalar(
        db,
        select(func.count(Attachment.id)).join(Email).where(*email_scope),
    )
    return email_count, attachment_count


async def _fetch_quality_issue_counts(
    db: AsyncSession, email_scope: list
) -> tuple[int, int, int]:
    missing_thread_count = await _count_scalar(
        db,
        select(func.count(Email.id)).where(
            *email_scope,
            or_(Email.thread_id.is_(None), Email.thread_id == ""),
        ),
    )
    missing_fingerprint_count = await _count_scalar(
        db,
        select(func.count(Email.id)).where(
            *email_scope,
            or_(Email.fingerprint.is_(None), Email.fingerprint == ""),
        ),
    )
    blank_attachment_count = await _count_scalar(
        db,
        select(func.count(Attachment.id))
        .join(Email)
        .where(
            *email_scope,
            or_(
                Attachment.content.is_(None),
                func.length(func.trim(Attachment.content)) == 0,
            ),
        ),
    )
    return missing_thread_count, missing_fingerprint_count, blank_attachment_count


async def _fetch_embedding_counts(
    db: AsyncSession, email_scope: list
) -> tuple[int, int]:
    embedded_email_count = await _count_scalar(
        db,
        select(func.count(Email.id)).where(*email_scope, Email.embedding.is_not(None)),
    )
    embedded_attachment_count = await _count_scalar(
        db,
        select(func.count(Attachment.id))
        .join(Email)
        .where(
            *email_scope,
            Attachment.embedding.is_not(None),
        ),
    )
    return embedded_email_count, embedded_attachment_count


async def _fetch_connector_events(
    db: AsyncSession, auth_context: AuthContext
) -> list[ConnectorSignalEvent]:
    connector_statement = _connector_scope_statement(auth_context)
    if connector_statement is not None:
        return await _scoped_rows(db, connector_statement)
    return []


async def _fetch_attachment_assets(db: AsyncSession, email_scope: list) -> list:
    attachment_asset_result = await db.execute(
        select(Attachment, Email)
        .join(Email)
        .where(*email_scope)
        .order_by(Email.date.desc(), Attachment.filename.asc())
        .limit(8)
    )
    return list(attachment_asset_result.all())


@router.get("/quality-surface", response_model=DataQualitySurfaceResponse)
async def get_data_quality_surface(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> DataQualitySurfaceResponse:
    webdav_accounts, project_folders = await _fetch_repositories(db, auth_context)
    email_scope = _email_scope_filter(auth_context)
    email_count, attachment_count = await _fetch_object_counts(db, email_scope)
    (
        missing_thread_count,
        missing_fingerprint_count,
        blank_attachment_count,
    ) = await _fetch_quality_issue_counts(db, email_scope)
    embedded_email_count, embedded_attachment_count = await _fetch_embedding_counts(
        db, email_scope
    )
    connector_events = await _fetch_connector_events(db, auth_context)
    attachment_asset_rows = await _fetch_attachment_assets(db, email_scope)

    source_count = len(webdav_accounts) + len(project_folders)
    embedded_total = embedded_email_count + embedded_attachment_count
    object_total = email_count + attachment_count
    return DataQualitySurfaceResponse(
        workspace_id=auth_context.workspace_id,
        organization_id=auth_context.organization_id,
        audit_event="data.quality_surface.viewed",
        provider_write_executed=False,
        repositories=_repository_summaries(
            webdav_accounts,
            project_folders,
            email_count,
            attachment_count,
        ),
        repository_assets=_repository_assets(attachment_asset_rows),
        pipeline_stages=_pipeline_stages(
            source_count=source_count,
            email_count=email_count,
            attachment_count=attachment_count,
            missing_thread_count=missing_thread_count,
            embedded_total=embedded_total,
            object_total=object_total,
            connector_event_count=len(connector_events),
        ),
        embedding_collections=_embedding_collections(
            email_count=email_count,
            embedded_email_count=embedded_email_count,
            attachment_count=attachment_count,
            embedded_attachment_count=embedded_attachment_count,
        ),
        quality_checks=_quality_checks(
            email_count=email_count,
            attachment_count=attachment_count,
            missing_thread_count=missing_thread_count,
            missing_fingerprint_count=missing_fingerprint_count,
            blank_attachment_count=blank_attachment_count,
            source_count=source_count,
            connector_event_count=len(connector_events),
        ),
        connector_events=[
            DataConnectorEvent(
                event_uid=event.event_uid,
                signal_key=event.signal_key,
                state_code=event.state_code,
                detail_text=event.detail_text,
                observed_at=_datetime_to_utc_iso(event.observed_at),
            )
            for event in connector_events
        ],
    )
