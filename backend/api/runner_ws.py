from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from typing import Dict

logger = logging.getLogger(__name__)

router = APIRouter(tags=["runner"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, token: str):
        await ws.accept()
        # In a real scenario, validate token against WorkspaceRunnerConfig
        self.active_connections[token] = ws
        safe_token = token.replace("\n", "").replace("\r", "")
        logger.info(f"Runner connected with token {safe_token}")

    def disconnect(self, token: str):
        if token in self.active_connections:
            del self.active_connections[token]
            safe_token = token.replace("\n", "").replace("\r", "")
            logger.info(f"Runner disconnected: {safe_token}")

manager = ConnectionManager()

@router.websocket("/ws/runner/{token}")
async def runner_endpoint(websocket: WebSocket, token: str):
    await manager.connect(websocket, token)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or process intents
            await websocket.send_text(f"Naruon ack: {data}")
    except WebSocketDisconnect:
        manager.disconnect(token)
