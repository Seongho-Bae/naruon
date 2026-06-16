import asyncio
import time
from pathlib import Path
import pytest

from services.email_import_service import _import_single_eml
from services.email_parser import EmailParseError

def setup_mock_eml():
    p = Path("test_mock.eml")
    p.write_bytes(b"From: a@b.com\nTo: b@c.com\nSubject: Test\n\nBody\n" * 1000)
    return p

async def run_naive(paths):
    # Simulate blocking the event loop
    pass

@pytest.mark.asyncio
async def test_benchmark_async_io():
    p = setup_mock_eml()

    def read_sync():
        time.sleep(0.01) # simulate slow I/O
        return p.read_bytes()

    async def task_sync():
        return read_sync()

    async def task_to_thread():
        return await asyncio.to_thread(read_sync)

    start = time.perf_counter()
    await asyncio.gather(*[task_sync() for _ in range(50)])
    sync_time = time.perf_counter() - start

    start = time.perf_counter()
    await asyncio.gather(*[task_to_thread() for _ in range(50)])
    thread_time = time.perf_counter() - start

    p.unlink()
    print(f"Sync time: {sync_time:.4f}s")
    print(f"Thread time: {thread_time:.4f}s")
