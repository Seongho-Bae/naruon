import asyncio
import time
from pathlib import Path

import pytest


def setup_mock_eml(tmp_path: Path) -> Path:
    p = tmp_path / "test_mock.eml"
    p.write_bytes(b"From: a@b.com\nTo: b@c.com\nSubject: Test\n\nBody\n" * 1000)
    return p

async def run_naive(paths):
    # Simulate blocking the event loop
    pass

@pytest.mark.asyncio
async def test_benchmark_async_io(tmp_path: Path):
    p = setup_mock_eml(tmp_path)

    def read_sync():
        time.sleep(0.01) # simulate slow I/O
        return p.read_bytes()

    async def task_sync():
        return read_sync()

    async def task_to_thread():
        return await asyncio.to_thread(read_sync)

    start = time.perf_counter()
    sync_results = await asyncio.gather(*[task_sync() for _ in range(50)])
    sync_time = time.perf_counter() - start

    start = time.perf_counter()
    thread_results = await asyncio.gather(*[task_to_thread() for _ in range(50)])
    thread_time = time.perf_counter() - start

    assert sync_results == thread_results
    assert thread_time < sync_time
