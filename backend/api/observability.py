import os
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import AuthContext, get_auth_context, is_admin_role, is_tenant_admin_role
from api.runner_config import _connector_manifest
from api.runner_ws import manager as runner_connection_manager
from core.config import settings
from db.models import WorkspaceRunnerConfig
from db.session import get_db

router = APIRouter(prefix="/api/observability", tags=["observability"])

SignalState = Literal[
    "enabled",
    "not_configured",
    "intent_only",
    "instrumentation_pending",
    "registration_configured",
    "not_registered",
]


class TelemetryRuntime(BaseModel):
    prometheus_metrics_enabled: bool
    otel_traces_enabled: bool
    otel_endpoint_configured: bool
    otel_endpoint_host: str | None


class ConnectorOperationalState(BaseModel):
    workspace_id: str
    registration_state: Literal["registration_configured", "not_registered"]
    connection_state: Literal["connected", "not_connected"]
    active_connection_count: int
    control_plane_domain: str
    network_mode: str
    runner_usage: str
    local_protocols: list[str]
    last_heartbeat_at: str | None
    last_disconnect_at: str | None
    queue_depth_state: Literal["not_reported"]


class OperationalSignal(BaseModel):
    signal_key: str
    display_name: str
    state: SignalState
    evidence_source: str
    detail: str
    provider_write_executed: bool = False


class OperationalSignalsResponse(BaseModel):
    workspace_id: str
    audit_event: Literal["observability.operational_signals.viewed"]
    telemetry: TelemetryRuntime
    connector: ConnectorOperationalState
    signals: list[OperationalSignal]


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _endpoint_host(endpoint: str | None) -> str | None:
    if not endpoint or not endpoint.strip():
        return None
    parsed = urlparse(endpoint.strip())
    if not parsed.netloc:
        return None
    return parsed.netloc.rsplit("@", 1)[-1]


def _check_org_admin(auth_context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not is_admin_role(auth_context.role):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "ORG_ADMIN_REQUIRED",
                "message": "Organization admin access required",
            },
        )
    if is_tenant_admin_role(auth_context.role) and not auth_context.organization_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "ORG_SCOPE_REQUIRED",
                "message": "Organization scope is required",
            },
        )
    if not auth_context.organization_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "ORG_SCOPE_REQUIRED",
                "message": "Organization scope is required",
            },
        )
    return auth_context


async def _get_runner_config(
    db: AsyncSession, organization_id: str
) -> WorkspaceRunnerConfig | None:
    result = await db.execute(
        select(WorkspaceRunnerConfig).where(
            WorkspaceRunnerConfig.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()


def _telemetry_runtime() -> TelemetryRuntime:
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_endpoint_configured = bool(otel_endpoint and otel_endpoint.strip())
    return TelemetryRuntime(
        prometheus_metrics_enabled=settings.ENABLE_PROMETHEUS_METRICS,
        otel_traces_enabled=_env_flag("ENABLE_OTEL") and otel_endpoint_configured,
        otel_endpoint_configured=otel_endpoint_configured,
        otel_endpoint_host=_endpoint_host(otel_endpoint),
    )


def _connector_state(
    organization_id: str, workspace_id: str, config: WorkspaceRunnerConfig | None
) -> ConnectorOperationalState:
    manifest = _connector_manifest()
    connection_snapshot = runner_connection_manager.snapshot(
        organization_id=organization_id,
        workspace_id=config.workspace_id if config is not None else workspace_id,
    )
    connection_state: Literal["connected", "not_connected"] = (
        "connected"
        if connection_snapshot.connection_state == "connected"
        else "not_connected"
    )
    registration_state: Literal["registration_configured", "not_registered"] = (
        "registration_configured"
        if config is not None and bool(config.registration_token)
        else "not_registered"
    )
    return ConnectorOperationalState(
        workspace_id=config.workspace_id if config is not None else workspace_id,
        registration_state=registration_state,
        connection_state=connection_state,
        active_connection_count=connection_snapshot.active_connection_count,
        control_plane_domain=str(manifest["control_plane_domain"]),
        network_mode=str(manifest["network_mode"]),
        runner_usage=str(manifest["runner_usage"]),
        local_protocols=list(manifest["local_protocols"]),
        last_heartbeat_at=connection_snapshot.last_seen_at,
        last_disconnect_at=connection_snapshot.last_disconnect_at,
        queue_depth_state="not_reported",
    )


def _operational_signals(
    telemetry: TelemetryRuntime, connector: ConnectorOperationalState
) -> list[OperationalSignal]:
    metrics_state: SignalState = (
        "enabled" if telemetry.prometheus_metrics_enabled else "not_configured"
    )
    traces_state: SignalState = (
        "enabled" if telemetry.otel_traces_enabled else "not_configured"
    )
    return [
        OperationalSignal(
            signal_key="prometheus_metrics",
            display_name="Prometheus metrics",
            state=metrics_state,
            evidence_source="ENABLE_PROMETHEUS_METRICS",
            detail="Prometheus /metrics exposure is opt-in and remains behind a trusted scrape path.",
        ),
        OperationalSignal(
            signal_key="otel_traces",
            display_name="OpenTelemetry traces",
            state=traces_state,
            evidence_source="ENABLE_OTEL and OTEL_EXPORTER_OTLP_ENDPOINT",
            detail="Trace export starts only when the OpenTelemetry flag and OTLP endpoint are both configured.",
        ),
        OperationalSignal(
            signal_key="connector_heartbeat",
            display_name="Connector heartbeat",
            state="enabled" if connector.connection_state == "connected" else connector.registration_state,
            evidence_source="runner WebSocket manager and workspace_runner_configs.registration_token",
            detail="Live heartbeat uses active outbound runner sockets; persistent heartbeat history is still planned.",
        ),
        OperationalSignal(
            signal_key="sync_lag",
            display_name="Sync lag",
            state="instrumentation_pending",
            evidence_source="IMAP, POP3, CalDAV, CardDAV, WebDAV workers",
            detail="Provider sync lag will be emitted by source-backed connector jobs, not inferred in the browser.",
        ),
        OperationalSignal(
            signal_key="provider_throttling",
            display_name="Provider throttling",
            state="instrumentation_pending",
            evidence_source="provider adapters",
            detail="Throttle and retry budgets require provider adapter events before dashboard claims are enabled.",
        ),
        OperationalSignal(
            signal_key="writeback_conflicts",
            display_name="Writeback conflicts",
            state="intent_only",
            evidence_source="calendar and WebDAV writeback-intent APIs",
            detail="Conflict handling is surfaced at intent boundaries until connector write execution records ETags.",
        ),
        OperationalSignal(
            signal_key="ai_action_audit",
            display_name="AI action audit",
            state="instrumentation_pending",
            evidence_source="task, mail, ontology, and WebDAV intent APIs",
            detail="Audit event names are returned by intent APIs; centralized trace correlation is still planned.",
        ),
    ]


@router.get("/operational-signals", response_model=OperationalSignalsResponse)
async def get_operational_signals(
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(_check_org_admin),
):
    organization_id = auth_context.organization_id
    if organization_id is None:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "ORG_SCOPE_REQUIRED",
                "message": "Organization scope is required",
            },
        )

    workspace_id = auth_context.workspace_id
    config = await _get_runner_config(db, organization_id)
    telemetry = _telemetry_runtime()
    connector = _connector_state(organization_id, workspace_id, config)
    return OperationalSignalsResponse(
        workspace_id=connector.workspace_id,
        audit_event="observability.operational_signals.viewed",
        telemetry=telemetry,
        connector=connector,
        signals=_operational_signals(telemetry, connector),
    )
