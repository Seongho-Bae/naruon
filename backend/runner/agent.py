import asyncio
import websockets
import sys

async def run_agent(token: str, url: str = "ws://127.0.0.1:8000/ws/runner"):
    ws_url = f"{url}/{token}"
    print(f"Connecting to {ws_url} ...")
    try:
        async with websockets.connect(ws_url) as websocket:
            print("Connected to Naruon Control Plane.")
            await websocket.send("Hello from Self-Hosted Runner!")
            response = await websocket.recv()
            print(f"Received from SaaS: {response}")
            
            # Listen for incoming tasks like "FETCH_MAIL" or "SEND_SMTP"
            while True:
                msg = await websocket.recv()
                print(f"Instruction received: {msg}")
                # Acknowledge or execute local proxy logic
                await websocket.send(f"Executed: {msg}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else "demo-token"
    asyncio.run(run_agent(token))
