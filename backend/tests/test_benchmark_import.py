import asyncio
import time
from pathlib import Path

import pytest


def setup_mock_eml(path: Path) -> Path:
    p = path
    p.write_bytes(b"From: a@b.com\nTo: b@c.com\nSubject: Test\n\nBody\n" * 1000)
    return p


@pytest.mark.asyncio
async def test_benchmark_async_io(tmp_path: Path):
    p = setup_mock_eml(tmp_path / "test_mock.eml")

    def read_sync():
        time.sleep(0.01)
        return p.read_bytes()

    async def task_sync():
        return read_sync()

    async def task_to_thread():
        return await asyncio.to_thread(read_sync)

    async def measure_event_loop_responsiveness(task_factory):
        tick_count = 0
        stop = False

        async def ticker():
            nonlocal tick_count
            while not stop:
                tick_count += 1
                await asyncio.sleep(0)

        ticker_task = asyncio.create_task(ticker())
        try:
            start = time.perf_counter()
            await asyncio.gather(*[task_factory() for _ in range(50)])
            elapsed = time.perf_counter() - start
        finally:
            stop = True
            await ticker_task
        return elapsed, tick_count

    try:
        sync_time, sync_tick_count = await measure_event_loop_responsiveness(task_sync)
        thread_time, thread_tick_count = await measure_event_loop_responsiveness(
            task_to_thread
        )
    finally:
        if p.exists():
            p.unlink()

    assert thread_tick_count > sync_tick_count
    assert thread_time < sync_time
