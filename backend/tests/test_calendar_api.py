from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from services.exceptions import CalendarServiceError


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_calendar_sync_endpoint_success(mock_create):
    mock_create.return_value = {"id": "123", "summary": "Test todo"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/calendar/sync",
            json={"todos": ["Test todo"], "user_token": {"token": "dummy"}},
        )

    assert response.status_code == 200
    assert response.json() == {
        "synced": 1,
        "events": [{"id": "123", "summary": "Test todo"}],
    }
    mock_create.assert_called_once_with("Test todo", {"token": "dummy"})


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_calendar_sync_endpoint_error(mock_create):
    mock_create.side_effect = CalendarServiceError("Mocked error")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/calendar/sync",
            json={"todos": ["Test todo"], "user_token": {"token": "dummy"}},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Mocked error"}
