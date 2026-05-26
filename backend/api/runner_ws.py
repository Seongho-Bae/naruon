import hashlib
import hmac
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from sqlalchemy import select

from api.auth import AuthContext, build_auth_context
from db.models import WorkspaceRunnerConfig
from db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["runner"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(
        self,
        ws: WebSocket,
        connection_key: str,
        auth_context: AuthContext,
    ):
        await ws.accept()
        self.active_connections[connection_key] = ws
        logger.info(
            "Runner connected for organization %s workspace %s",
            auth_context.organization_id,
            auth_context.workspace_id,
        )

    def disconnect(self, connection_key: str):
        if connection_key in self.active_connections:
            del self.active_connections[connection_key]
            logger.info("Runner disconnected: %s", connection_key)


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
            # Echo back or process intents
            await websocket.send_text(f"Naruon ack: {data}")
    except WebSocketDisconnect:
        manager.disconnect(connection_key)
