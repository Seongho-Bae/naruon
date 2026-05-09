import asyncio
import contextlib
import signal

from services.imap_worker import ImapSyncWorker


async def run_worker() -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signame in ("SIGINT", "SIGTERM"):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(getattr(signal, signame), stop_event.set)

    worker = ImapSyncWorker()
    await worker.start()
    try:
        await stop_event.wait()
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
