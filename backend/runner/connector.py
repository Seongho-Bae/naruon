import asyncio
import json
import logging
from typing import Dict, Any

try:
    import websockets
except ImportError:
    # Optional dependency for the runner
    websockets = None

logger = logging.getLogger(__name__)

class SelfHostedConnector:
    def __init__(self, target_ws_url: str, token: str):
        self.target_ws_url = target_ws_url
        self.token = token
        self.connection = None
        self.is_connected = False
        
    async def connect(self):
        if websockets is None:
            logger.error("websockets library is not installed. Runner cannot start.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            self.connection = await websockets.connect(self.target_ws_url, additional_headers=headers)
            self.is_connected = True
            logger.info(f"Connected to Naruon Gateway at {self.target_ws_url}")
            await self._listen_loop()
        except asyncio.CancelledError:
            raise
        except (ConnectionRefusedError, OSError, asyncio.TimeoutError) as e:
            self.is_connected = False
            logger.exception(f"Failed to connect to Naruon Gateway: {e}")
        except Exception as e:
            # We catch Exception here but limit logger.exception to websocket errors
            # to avoid referencing websockets.exceptions directly in the tuple
            # in case websockets is None (though we return early if it is)
            if websockets and isinstance(e, websockets.exceptions.WebSocketException):
                self.is_connected = False
                logger.exception(f"Failed to connect to Naruon Gateway: {e}")
            else:
                self.is_connected = False
                logger.exception(f"Failed to connect to Naruon Gateway with unexpected error: {e}")

    async def _listen_loop(self):
        if not self.connection:
            return
        try:
            while self.is_connected:
                message = await self.connection.recv()
                await self.handle_message(message)
        except Exception as e:
            if websockets and isinstance(e, websockets.exceptions.ConnectionClosed):
                logger.warning("Connection closed by remote gateway.")
            else:
                logger.warning(f"Connection loop ended: {e}")
            self.is_connected = False
            
    async def handle_message(self, message: str | bytes):
        # Dispatch message to internal SMTP/IMAP proxy handlers
        logger.debug("Received instruction from gateway.")
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.error("Failed to decode message from gateway.")
            await self.send_response({
                "status": "error",
                "action": None,
                "error": "invalid json",
            })
            return

        if not isinstance(payload, dict):
            logger.error("Gateway instruction payload must be an object.")
            await self.send_response({
                "status": "error",
                "action": None,
                "error": "invalid payload",
            })
            return

        action = payload.get("action")
        if action == "fetch_imap":
            await self._handle_fetch_imap(payload)
        elif action == "send_smtp":
            await self._handle_send_smtp(payload)
        else:
            logger.info("Unknown action received.")
            await self.send_response({
                "status": "error",
                "action": action if isinstance(action, str) else None,
                "error": "unknown action",
            })
            
    async def _handle_fetch_imap(self, payload: Dict[str, Any]):
        if not payload.get("account"):
            logger.error("IMAP fetch instruction is missing account.")
            await self.send_response({
                "status": "error",
                "action": "fetch_imap",
                "error": "missing account",
            })
            return
        logger.info("Executing local IMAP fetch for configured account.")
        # Placeholder for actual internal IMAP logic
        await self.send_response({"status": "success", "action": "fetch_imap", "data": "IMAP data placeholder"})
        
    async def _handle_send_smtp(self, payload: Dict[str, Any]):
        if not payload.get("account"):
            logger.error("SMTP send instruction is missing account.")
            await self.send_response({
                "status": "error",
                "action": "send_smtp",
                "error": "missing account",
            })
            return
        logger.info("Executing local SMTP send for configured account.")
        # Placeholder for actual internal SMTP logic
        await self.send_response({"status": "success", "action": "send_smtp", "message_id": "mock_id_123"})

    async def send_response(self, response: Dict[str, Any]):
        if self.is_connected and self.connection:
            await self.connection.send(json.dumps(response))

if __name__ == "__main__":
    # Example usage for local bootstrap
    connector = SelfHostedConnector("ws://localhost:8080/api/runner/ws", "sample-token")
    asyncio.run(connector.connect())
