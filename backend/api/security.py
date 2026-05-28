from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import (
    AuthContext,
    get_auth_context,
    is_admin_role,
    is_system_admin_role,
    is_tenant_admin_role,
)
from db.models import CalendarWritebackSource, ConnectorSignalEvent, WebdavAccount
from db.session import get_db
from services.access_policy import AccessRequest, ResourcePolicy, evaluate_access

router = APIRouter(prefix="/api/security", tags=["security"])

SourceType = Literal["caldav_source", "carddav_source", "webdav_repository"]
DecisionReason = Literal[
    "allowed",
    "organization_denied",
    "data_region_denied",
    "consent_denied",
    "ownership_denied",
    "rbac_denied",
]


class ViewerContext(BaseModel):
    user_id: str
    role: str
    organization_id: str | None
    group_ids: list[str]
    workspace_id: str


class PolicyDecisionSummary(BaseModel):
    decision_uid: str
    resource_label: str
    resource_type: str
    allowed: bool
    reason: DecisionReason
    evidence_source: str


class GovernanceSource(BaseModel):
    source_id: str
    source_type: SourceType
    source_label: str
    source_host: str
    owner_id: str
    organization_id: str | None
    workspace_id: str
    capabilities: list[str]
    writeback_enabled: bool
    provider_write_executed: bool
    policy_decision: PolicyDecisionSummary
    last_observed_at: str | None


class ConnectorEvidence(BaseModel):
    event_uid: str
    signal_key: str
    state_code: str
    detail_text: str | None
    observed_at: str


class ExternalShareReview(BaseModel):
    review_uid: str
    source_id: str
    source_type: SourceType
    review_label: str
    exposure_level: Literal["internal", "external_writeback"]
    decision_reason: DecisionReason
    provider_write_executed: bool


class PolicyOrderStep(BaseModel):
    step_key: str
    display_name: str
    evidence_source: str


class SecurityAccessSurfaceResponse(BaseModel):
    workspace_id: str
    organization_id: str | None
    audit_event: Literal["security.access_surface.viewed"]
    viewer: ViewerContext
    sources: list[GovernanceSource]
    connector_events: list[ConnectorEvidence]
    policy_decisions: list[PolicyDecisionSummary]
    external_share_reviews: list[ExternalShareReview]
    policy_order: list[PolicyOrderStep]


def _datetime_to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _host_from_url(value: str) -> str:
    parsed = urlparse(value)
    return parsed.netloc.rsplit("@", 1)[-1] if parsed.netloc else value


def _can_read_org_scope(auth_context: AuthContext) -> bool:
    return (
        is_admin_role(auth_context.role)
        and auth_context.organization_id is not None
    )


def _webdav_scope_statement(auth_context: AuthContext):
    statement = select(WebdavAccount).order_by(
        WebdavAccount.created_at.asc(),
        WebdavAccount.source_uid.asc(),
    )
    if _can_read_org_scope(auth_context):
        return statement.where(WebdavAccount.organization_id == auth_context.organization_id)
    organization_filter = (
        WebdavAccount.organization_id == auth_context.organization_id
        if auth_context.organization_id is not None
        else WebdavAccount.organization_id.is_(None)
    )
    return statement.where(
        WebdavAccount.user_id == auth_context.user_id,
        organization_filter,
    )


def _calendar_scope_statement(auth_context: AuthContext):
    statement = (
        select(CalendarWritebackSource)
        .where(CalendarWritebackSource.source_protocol.in_(("caldav", "carddav")))
        .order_by(
            CalendarWritebackSource.created_at.asc(),
            CalendarWritebackSource.source_uid.asc(),
        )
    )
    if _can_read_org_scope(auth_context):
        return statement.where(
            CalendarWritebackSource.organization_id == auth_context.organization_id
        )
    organization_filter = (
        CalendarWritebackSource.organization_id == auth_context.organization_id
        if auth_context.organization_id is not None
        else CalendarWritebackSource.organization_id.is_(None)
    )
    return statement.where(
        CalendarWritebackSource.user_id == auth_context.user_id,
        organization_filter,
    )


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


def _source_in_scope(
    auth_context: AuthContext,
    owner_id: str,
    organization_id: str | None,
) -> bool:
    if _can_read_org_scope(auth_context):
        return organization_id == auth_context.organization_id
    return (
        owner_id == auth_context.user_id
        and organization_id == auth_context.organization_id
    )


def _access_request(auth_context: AuthContext) -> AccessRequest:
    return AccessRequest(
        user_id=auth_context.user_id,
        role=auth_context.role,
        organization_id=auth_context.organization_id,
        group_ids=auth_context.group_ids,
        data_region="kr",
        consent_scopes=("mail.read", "calendar.read", "webdav.write"),
    )


def _decision_summary(
    *,
    decision_uid: str,
    resource_label: str,
    resource_type: str,
    auth_context: AuthContext,
    resource: ResourcePolicy,
    evidence_source: str,
) -> PolicyDecisionSummary:
    decision = evaluate_access(_access_request(auth_context), resource)
    return PolicyDecisionSummary(
        decision_uid=decision_uid,
        resource_label=resource_label,
        resource_type=resource_type,
        allowed=decision.allowed,
        reason=decision.reason,
        evidence_source=evidence_source,
    )


def _source_policy(
    auth_context: AuthContext,
    owner_id: str,
    organization_id: str | None,
    writeback_enabled: bool,
) -> ResourcePolicy:
    delegated_user_ids: tuple[str, ...] = (
        (auth_context.user_id,)
        if is_admin_role(auth_context.role) and organization_id == auth_context.organization_id
        else ()
    )
    required_consent = ("webdav.write",) if writeback_enabled else ()
    return ResourcePolicy(
        owner_id=owner_id,
        organization_id=organization_id,
        permitted_roles=("tenant_admin", "organization_admin", "group_admin", "member"),
        permitted_group_ids=auth_context.group_ids,
        data_region="kr",
        required_consent_scopes=required_consent,
        delegated_user_ids=delegated_user_ids,
    )


def _webdav_source(
    account: WebdavAccount, auth_context: AuthContext
) -> GovernanceSource:
    decision = _decision_summary(
        decision_uid=f"policy:{account.source_uid}",
        resource_label="WebDAV repository",
        resource_type="webdav_repository",
        auth_context=auth_context,
        resource=_source_policy(
            auth_context,
            account.user_id,
            account.organization_id,
            bool(account.writeback_enabled),
        ),
        evidence_source="webdav_accounts",
    )
    return GovernanceSource(
        source_id=account.source_uid,
        source_type="webdav_repository",
        source_label="WebDAV repository",
        source_host=_host_from_url(account.server_url),
        owner_id=account.user_id,
        organization_id=account.organization_id,
        workspace_id=auth_context.workspace_id,
        capabilities=["read", "write", "etag"] if account.writeback_enabled else ["read"],
        writeback_enabled=bool(account.writeback_enabled),
        provider_write_executed=False,
        policy_decision=decision,
        last_observed_at=_datetime_to_utc_iso(account.created_at),
    )


def _calendar_source(
    source: CalendarWritebackSource, auth_context: AuthContext
) -> GovernanceSource:
    source_type: SourceType = (
        "carddav_source" if source.source_protocol == "carddav" else "caldav_source"
    )
    decision = _decision_summary(
        decision_uid=f"policy:{source.source_uid}",
        resource_label=f"{source.provider_name} {source.source_protocol.upper()} source",
        resource_type=source_type,
        auth_context=auth_context,
        resource=_source_policy(
            auth_context,
            source.user_id,
            source.organization_id,
            bool(source.writeback_enabled),
        ),
        evidence_source="calendar_writeback_sources",
    )
    capabilities = ["read"]
    if source.writeback_enabled:
        capabilities.extend(["write", "etag"])
    return GovernanceSource(
        source_id=source.source_uid,
        source_type=source_type,
        source_label=source.provider_name,
        source_host=source.source_host,
        owner_id=source.user_id,
        organization_id=source.organization_id,
        workspace_id=source.workspace_id,
        capabilities=capabilities,
        writeback_enabled=bool(source.writeback_enabled),
        provider_write_executed=False,
        policy_decision=decision,
        last_observed_at=_datetime_to_utc_iso(source.created_at),
    )


def _connector_evidence(event: ConnectorSignalEvent) -> ConnectorEvidence:
    return ConnectorEvidence(
        event_uid=event.event_uid,
        signal_key=event.signal_key,
        state_code=event.state_code,
        detail_text=event.detail_text,
        observed_at=_datetime_to_utc_iso(event.observed_at),
    )


def _canonical_policy_decisions(
    auth_context: AuthContext,
    source_decisions: list[PolicyDecisionSummary],
) -> list[PolicyDecisionSummary]:
    decisions = list(source_decisions)
    decisions.append(
        _decision_summary(
            decision_uid="policy:cross-organization-deny",
            resource_label="Cross-organization provider secret",
            resource_type="provider_secret",
            auth_context=auth_context,
            resource=ResourcePolicy(
                owner_id=auth_context.user_id,
                organization_id="org-outside-scope",
                permitted_roles=("tenant_admin", "organization_admin"),
                permitted_group_ids=(),
                data_region="kr",
                required_consent_scopes=(),
            ),
            evidence_source="access_policy.evaluate_access",
        )
    )
    decisions.append(
        _decision_summary(
            decision_uid="policy:data-region-deny",
            resource_label="Regional export outside policy",
            resource_type="data_export",
            auth_context=auth_context,
            resource=ResourcePolicy(
                owner_id=auth_context.user_id,
                organization_id=auth_context.organization_id,
                permitted_roles=("tenant_admin", "organization_admin", "member"),
                permitted_group_ids=auth_context.group_ids,
                data_region="eu",
                required_consent_scopes=(),
            ),
            evidence_source="access_policy.evaluate_access",
        )
    )
    return decisions


def _share_reviews(sources: list[GovernanceSource]) -> list[ExternalShareReview]:
    return [
        ExternalShareReview(
            review_uid=f"share:{source.source_id}",
            source_id=source.source_id,
            source_type=source.source_type,
            review_label=f"{source.source_label} writeback boundary",
            exposure_level="external_writeback"
            if source.writeback_enabled
            else "internal",
            decision_reason=source.policy_decision.reason,
            provider_write_executed=False,
        )
        for source in sources
    ]


def _policy_order() -> list[PolicyOrderStep]:
    return [
        PolicyOrderStep(
            step_key="signed_session",
            display_name="Signed session identity",
            evidence_source="api.auth.get_auth_context",
        ),
        PolicyOrderStep(
            step_key="organization_scope",
            display_name="Organization and workspace scope",
            evidence_source="organization_id and workspace_id claims",
        ),
        PolicyOrderStep(
            step_key="data_region",
            display_name="Data-region deny",
            evidence_source="services.access_policy.evaluate_access",
        ),
        PolicyOrderStep(
            step_key="consent",
            display_name="Consent and source capability deny",
            evidence_source="services.access_policy.evaluate_access",
        ),
        PolicyOrderStep(
            step_key="ownership",
            display_name="Owner or delegated admin boundary",
            evidence_source="services.access_policy.evaluate_access",
        ),
        PolicyOrderStep(
            step_key="rbac",
            display_name="RBAC allow after ABAC denies",
            evidence_source="services.access_policy.evaluate_access",
        ),
    ]


@router.get("/access-surface", response_model=SecurityAccessSurfaceResponse)
async def get_access_surface(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> SecurityAccessSurfaceResponse:
    webdav_result = await db.execute(_webdav_scope_statement(auth_context))
    calendar_result = await db.execute(_calendar_scope_statement(auth_context))
    connector_statement = _connector_scope_statement(auth_context)
    connector_events: list[ConnectorSignalEvent] = []
    if connector_statement is not None:
        connector_result = await db.execute(connector_statement)
        connector_events = [
            event
            for event in connector_result.scalars().all()
            if event.organization_id == auth_context.organization_id
            and event.workspace_id == auth_context.workspace_id
        ]

    sources = [
        _webdav_source(account, auth_context)
        for account in webdav_result.scalars().all()
        if _source_in_scope(auth_context, account.user_id, account.organization_id)
    ]
    sources.extend(
        _calendar_source(source, auth_context)
        for source in calendar_result.scalars().all()
        if _source_in_scope(auth_context, source.user_id, source.organization_id)
    )
    source_decisions = [source.policy_decision for source in sources]
    policy_decisions = _canonical_policy_decisions(auth_context, source_decisions)

    return SecurityAccessSurfaceResponse(
        workspace_id=auth_context.workspace_id,
        organization_id=auth_context.organization_id,
        audit_event="security.access_surface.viewed",
        viewer=ViewerContext(
            user_id=auth_context.user_id,
            role=auth_context.role,
            organization_id=auth_context.organization_id,
            group_ids=list(auth_context.group_ids),
            workspace_id=auth_context.workspace_id,
        ),
        sources=sources,
        connector_events=[_connector_evidence(event) for event in connector_events],
        policy_decisions=policy_decisions,
        external_share_reviews=_share_reviews(sources),
        policy_order=_policy_order(),
    )
