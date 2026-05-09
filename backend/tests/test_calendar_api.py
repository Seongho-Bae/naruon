from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock
from services.exceptions import CalendarServiceError
from api.auth import get_current_user

client = TestClient(app)


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_endpoint_success(mock_create):
    # Setup mock
    mock_create.return_value = {"id": "123", "summary": "Test todo"}

    response = client.post(
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
def test_calendar_sync_endpoint_error(mock_create):
    mock_create.side_effect = CalendarServiceError("Mocked error")

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"], "user_token": {"token": "dummy"}},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Calendar sync failed"}


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_uses_current_user_dependency(mock_create):
    called = False

    async def override_current_user():
        nonlocal called
        called = True
        return "calendar-user"

    app.dependency_overrides[get_current_user] = override_current_user
    mock_create.return_value = {"id": "123", "summary": "Test todo"}

    try:
        response = client.post(
            "/api/calendar/sync",
            json={"todos": ["Test todo"], "user_token": {"token": "dummy"}},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert called is True
