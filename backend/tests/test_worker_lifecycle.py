import pytest
from fastapi import FastAPI
from unittest.mock import AsyncMock

from main import lifespan


@pytest.mark.asyncio
async def test_lifespan_starts_and_stops_imap_and_pop3_workers(monkeypatch):
    imap_start = AsyncMock()
    imap_stop = AsyncMock()
    pop3_start = AsyncMock()
    pop3_stop = AsyncMock()

    monkeypatch.setattr("main.DISABLE_WORKERS", False)
    monkeypatch.setattr("main.imap_worker.start", imap_start)
    monkeypatch.setattr("main.imap_worker.stop", imap_stop)
    monkeypatch.setattr("main.pop3_worker.start", pop3_start)
    monkeypatch.setattr("main.pop3_worker.stop", pop3_stop)

    async with lifespan(FastAPI()):
        pass

    imap_start.assert_awaited_once()
    pop3_start.assert_awaited_once()
    imap_stop.assert_awaited_once()
    pop3_stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_stops_started_worker_when_pop3_start_fails(monkeypatch):
    imap_start = AsyncMock()
    imap_stop = AsyncMock()
    pop3_start = AsyncMock(side_effect=RuntimeError("pop3 failed"))
    pop3_stop = AsyncMock()

    monkeypatch.setattr("main.DISABLE_WORKERS", False)
    monkeypatch.setattr("main.imap_worker.start", imap_start)
    monkeypatch.setattr("main.imap_worker.stop", imap_stop)
    monkeypatch.setattr("main.pop3_worker.start", pop3_start)
    monkeypatch.setattr("main.pop3_worker.stop", pop3_stop)

    with pytest.raises(RuntimeError, match="pop3 failed"):
        async with lifespan(FastAPI()):
            pass

    imap_start.assert_awaited_once()
    pop3_start.assert_awaited_once()
    imap_stop.assert_awaited_once()
    pop3_stop.assert_not_awaited()


@pytest.mark.asyncio
async def test_lifespan_stops_workers_when_app_context_raises(monkeypatch):
    imap_start = AsyncMock()
    imap_stop = AsyncMock()
    pop3_start = AsyncMock()
    pop3_stop = AsyncMock()

    monkeypatch.setattr("main.DISABLE_WORKERS", False)
    monkeypatch.setattr("main.imap_worker.start", imap_start)
    monkeypatch.setattr("main.imap_worker.stop", imap_stop)
    monkeypatch.setattr("main.pop3_worker.start", pop3_start)
    monkeypatch.setattr("main.pop3_worker.stop", pop3_stop)

    with pytest.raises(RuntimeError, match="app failed"):
        async with lifespan(FastAPI()):
            raise RuntimeError("app failed")

    imap_stop.assert_awaited_once()
    pop3_stop.assert_awaited_once()
