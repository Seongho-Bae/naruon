import asyncio
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
            self.connection = await websockets.connect(
                self.target_ws_url, additional_headers=headers
            )
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
                logger.exception(
                    f"Failed to connect to Naruon Gateway with unexpected error: {e}"
                )

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
        logger.debug(f"Received instruction from gateway: {message}")
        pass

    async def send_response(self, response: Dict[str, Any]):
        if self.is_connected and self.connection:
            import json

            await self.connection.send(json.dumps(response))


if __name__ == "__main__":
    # Example usage for local bootstrap
    connector = SelfHostedConnector("ws://localhost:8080/api/runner/ws", "sample-token")
    asyncio.run(connector.connect())
