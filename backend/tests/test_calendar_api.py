from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock
from services.exceptions import CalendarServiceError

client = TestClient(app, headers={"X-User-Id": "testuser"})


def test_calendar_sync_rejects_missing_authentication():
    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"], "user_token": {"token": "attacker-supplied"}},
    )

    assert response.status_code == 401


@patch("api.calendar.get_calendar_credentials_for_user")
@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_endpoint_success(mock_create, mock_get_credentials):
    # Setup mock
    mock_get_credentials.return_value = {"token": "server-side-token"}
    mock_create.return_value = {"id": "123", "summary": "Test todo"}

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "synced": 1,
        "events": [{"id": "123", "summary": "Test todo"}],
    }
    mock_get_credentials.assert_called_once()
    called_token = mock_create.call_args.args[1]
    assert called_token == {"token": "server-side-token"}


@patch("api.calendar.get_calendar_credentials_for_user")
@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_rejects_body_tokens_when_server_credentials_missing(
    mock_create, mock_get_credentials
):
    mock_get_credentials.return_value = None

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"], "user_token": {"token": "attacker-supplied"}},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Calendar credentials are not configured for this user"
    }
    mock_create.assert_not_called()


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
@patch("api.calendar.get_calendar_credentials_for_user")
def test_calendar_sync_endpoint_error(mock_get_credentials, mock_create):
    mock_get_credentials.return_value = {"token": "server-side-token"}
    mock_create.side_effect = CalendarServiceError("Mocked error")

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"]},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Mocked error"}
