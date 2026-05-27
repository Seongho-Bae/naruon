import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from api.auth import AuthContext, build_auth_context
from db.models import ConnectorSignalEvent, WorkspaceRunnerConfig
from db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["runner"])


@dataclass(frozen=True)
class RunnerConnectionRecord:
    organization_id: str
    workspace_id: str
    connected_at: str


@dataclass(frozen=True)
class RunnerConnectionSnapshot:
    organization_id: str
    workspace_id: str
    connection_state: str
    active_connection_count: int
    last_seen_at: str | None
    last_disconnect_at: str | None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.connection_records: dict[str, RunnerConnectionRecord] = {}
        self.last_seen_by_org: dict[str, str] = {}
        self.last_disconnect_by_org: dict[str, str] = {}

    async def connect(
        self,
        ws: WebSocket,
        connection_key: str,
        auth_context: AuthContext,
    ):
        await ws.accept()
        organization_id = auth_context.organization_id
        if not organization_id:
            raise _policy_violation()
        now = _utc_now_iso()
        self.active_connections[connection_key] = ws
        self.connection_records[connection_key] = RunnerConnectionRecord(
            organization_id=organization_id,
            workspace_id=auth_context.workspace_id,
            connected_at=now,
        )
        self.last_seen_by_org[organization_id] = now
        logger.info(
            "Runner connected for organization %s workspace %s",
            organization_id,
            auth_context.workspace_id,
        )
        await _record_connector_signal_event_safely(
            organization_id=organization_id,
            workspace_id=auth_context.workspace_id,
            signal_key="connector_heartbeat",
            state_code="connected",
            detail_text="outbound runner socket connected",
        )

    async def disconnect(self, connection_key: str):
        record = self.connection_records.pop(connection_key, None)
        if connection_key in self.active_connections:
            del self.active_connections[connection_key]
        if record:
            disconnected_at = _utc_now_iso()
            self.last_disconnect_by_org[record.organization_id] = disconnected_at
            logger.info(
                "Runner disconnected for organization %s workspace %s",
                record.organization_id,
                record.workspace_id,
            )
            await _record_connector_signal_event_safely(
                organization_id=record.organization_id,
                workspace_id=record.workspace_id,
                signal_key="connector_heartbeat",
                state_code="disconnected",
                detail_text="outbound runner socket disconnected",
            )

    async def touch(self, connection_key: str):
        record = self.connection_records.get(connection_key)
        if record:
            self.last_seen_by_org[record.organization_id] = _utc_now_iso()
            await _record_connector_signal_event_safely(
                organization_id=record.organization_id,
                workspace_id=record.workspace_id,
                signal_key="connector_heartbeat",
                state_code="heartbeat",
                detail_text="outbound runner heartbeat received",
            )

    def snapshot(
        self, organization_id: str, workspace_id: str
    ) -> RunnerConnectionSnapshot:
        active_records = [
            record
            for record in self.connection_records.values()
            if record.organization_id == organization_id
        ]
        active_count = len(active_records)
        last_seen_candidates = [
            candidate
            for candidate in [self.last_seen_by_org.get(organization_id)]
            if candidate
        ]
        if active_records:
            last_seen_candidates.extend(record.connected_at for record in active_records)
        last_seen_at = max(last_seen_candidates) if last_seen_candidates else None
        return RunnerConnectionSnapshot(
            organization_id=organization_id,
            workspace_id=active_records[0].workspace_id if active_records else workspace_id,
            connection_state="connected" if active_count else "not_connected",
            active_connection_count=active_count,
            last_seen_at=last_seen_at,
            last_disconnect_at=self.last_disconnect_by_org.get(organization_id),
        )

    def reset(self):
        self.active_connections.clear()
        self.connection_records.clear()
        self.last_seen_by_org.clear()
        self.last_disconnect_by_org.clear()


manager = ConnectionManager()


def _policy_violation() -> WebSocketException:
    return WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


def _auth_context_from_websocket(websocket: WebSocket) -> AuthContext:
    try:
        return build_auth_context(websocket.headers.get("authorization"))
    except HTTPException as exc:
        raise _policy_violation() from exc


async def _registered_runner_token(organization_id: str) -> str | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WorkspaceRunnerConfig.registration_token).where(
                WorkspaceRunnerConfig.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()


async def record_connector_signal_event(
    *,
    organization_id: str,
    workspace_id: str,
    signal_key: str,
    state_code: str,
    detail_text: str,
) -> None:
    async with AsyncSessionLocal() as db:
        db.add(
            ConnectorSignalEvent(
                organization_id=organization_id,
                workspace_id=workspace_id,
                signal_key=signal_key,
                state_code=state_code,
                detail_text=detail_text,
            )
        )
        await db.commit()


async def _record_connector_signal_event_safely(
    *,
    organization_id: str,
    workspace_id: str,
    signal_key: str,
    state_code: str,
    detail_text: str,
) -> None:
    try:
        await record_connector_signal_event(
            organization_id=organization_id,
            workspace_id=workspace_id,
            signal_key=signal_key,
            state_code=state_code,
            detail_text=detail_text,
        )
    except SQLAlchemyError:
        logger.debug("Runner signal event persistence skipped", exc_info=True)


async def _runner_connection_key(token: str, auth_context: AuthContext) -> str:
    if not token or not auth_context.organization_id:
        raise _policy_violation()

    registered_token = await _registered_runner_token(auth_context.organization_id)
    if not registered_token or not hmac.compare_digest(registered_token, token):
        raise _policy_violation()

    token_fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    return f"{auth_context.organization_id}:{token_fingerprint}"


@router.websocket("/ws/runner/{token}")
async def runner_endpoint(websocket: WebSocket, token: str):
    auth_context = _auth_context_from_websocket(websocket)
    connection_key = await _runner_connection_key(token, auth_context)
    await manager.connect(websocket, connection_key, auth_context)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.touch(connection_key)
            # Echo back or process intents
            await websocket.send_text(f"Naruon ack: {data}")
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(connection_key)
