import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock
from services.exceptions import CalendarServiceError

client = TestClient(app, headers={"X-User-Id": "testuser"})
workspace_client = TestClient(
    app,
    headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
)


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


def test_calendar_writeback_intent_uses_customer_owned_caldav_account():
    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "sources": [
                {
                    "source_id": "naruon-internal-cache",
                    "provider": "naruon",
                    "protocol": "local",
                    "owner_id": "testuser",
                    "capabilities": ["read"],
                    "writeback_enabled": False,
                },
                {
                    "source_id": "calendar-primary",
                    "provider": "fastmail",
                    "protocol": "caldav",
                    "owner_id": "testuser",
                    "capabilities": ["read", "write", "etag"],
                    "writeback_enabled": True,
                    "etag": "abc123",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "workspace_id": "workspace-org-acme",
        "target_source_id": "calendar-primary",
        "protocol": "caldav",
        "writeback_mode": "customer_owned",
        "requires_if_match": False,
        "if_match": None,
        "provenance": {
            "created_by": "testuser",
            "source_provider": "fastmail",
            "source_protocol": "caldav",
        },
        "audit_event": "calendar.writeback_intent.created",
    }


def test_calendar_writeback_update_requires_etag_if_match():
    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "update",
            "summary": "Launch review",
            "sources": [
                {
                    "source_id": "calendar-primary",
                    "provider": "fastmail",
                    "protocol": "caldav",
                    "owner_id": "testuser",
                    "capabilities": ["read", "write", "etag"],
                    "writeback_enabled": True,
                    "etag": "abc123",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["requires_if_match"] is True
    assert data["if_match"] == "abc123"


def test_calendar_writeback_rejects_non_owner_and_naruon_only_storage():
    non_owner_response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "sources": [
                {
                    "source_id": "shared-calendar",
                    "provider": "fastmail",
                    "protocol": "caldav",
                    "owner_id": "other-user",
                    "capabilities": ["read", "write", "etag"],
                    "writeback_enabled": True,
                    "etag": "abc123",
                }
            ],
        },
    )
    assert non_owner_response.status_code == 403

    naruon_only_response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "sources": [
                {
                    "source_id": "naruon-cache",
                    "provider": "naruon",
                    "protocol": "local",
                    "owner_id": "testuser",
                    "capabilities": ["read", "write"],
                    "writeback_enabled": True,
                }
            ],
        },
    )
    assert naruon_only_response.status_code == 422
