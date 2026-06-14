import asyncio
import websockets
import sys
import os
import logging

logger = logging.getLogger(__name__)

async def run_agent(token: str, url: str = "ws://127.0.0.1:8000/ws/runner"):
    ws_url = f"{url}/{token}"
    logger.info(f"Connecting to {ws_url} ...")
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info("Connected to Naruon Control Plane.")
            await websocket.send("Hello from Self-Hosted Runner!")
            response = await websocket.recv()
            logger.info(f"Received from SaaS: {response}")
            
            # Listen for incoming tasks like "FETCH_MAIL" or "SEND_SMTP"
            while True:
                msg = await websocket.recv()
                logger.info(f"Instruction received: {msg}")
                # Acknowledge or execute local proxy logic
                await websocket.send(f"Executed: {msg}")
    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    token = os.environ.get("RUNNER_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]

    if not token:
        logger.error("No token provided. Please set the RUNNER_TOKEN environment variable or provide it as a CLI argument.")
        sys.exit(1)

    asyncio.run(run_agent(token))
