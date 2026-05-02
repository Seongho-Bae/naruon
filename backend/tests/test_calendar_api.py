from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock
from services.exceptions import CalendarServiceError

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
    assert response.json() == {"detail": "Mocked error"}


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_requires_bearer_authentication(mock_create):
    mock_create.return_value = {"id": "123", "summary": "Test todo"}

    with patch.dict(app.dependency_overrides, {}, clear=True):
        response = client.post(
            "/api/calendar/sync",
            json={"todos": ["Test todo"], "user_token": {"token": "dummy"}},
        )

    assert response.status_code == 401
    mock_create.assert_not_called()
