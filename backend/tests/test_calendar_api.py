import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock
from api import calendar as calendar_api
from api.calendar import WritebackSource
from services.exceptions import CalendarServiceError

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")

client = TestClient(app, headers={"X-User-Id": "testuser"})
workspace_client = TestClient(
    app,
    headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
)


@pytest.fixture
def writeback_source_override():
    def apply(sources: list[WritebackSource]) -> None:
        async def source_override() -> tuple[WritebackSource, ...]:
            return tuple(sources)

        app.dependency_overrides[calendar_api.get_writeback_sources] = source_override

    yield apply
    if hasattr(calendar_api, "get_writeback_sources"):
        app.dependency_overrides.pop(calendar_api.get_writeback_sources, None)


@pytest.fixture
def calendar_user_token_override():
    def apply(token: dict[str, str]) -> None:
        async def token_override() -> dict[str, str]:
            return token

        app.dependency_overrides[calendar_api.get_calendar_user_token] = token_override

    yield apply
    app.dependency_overrides.pop(calendar_api.get_calendar_user_token, None)


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_endpoint_success(mock_create, calendar_user_token_override):
    # Setup mock
    mock_create.return_value = {"id": "123", "summary": "Test todo"}
    calendar_user_token_override({"token": "server-owned"})

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "synced": 1,
        "events": [{"id": "123", "summary": "Test todo"}],
    }
    mock_create.assert_called_once_with("Test todo", {"token": "server-owned"})


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_rejects_client_supplied_user_token(mock_create):
    mock_create.return_value = {"id": "attacker-event"}

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"], "user_token": {"token": "attacker"}},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"
    mock_create.assert_not_called()


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_uses_server_authoritative_calendar_credentials(mock_create):
    mock_create.return_value = {"id": "123", "summary": "Test todo"}

    async def token_override():
        return {"token": "server-owned"}

    app.dependency_overrides[calendar_api.get_calendar_user_token] = token_override
    try:
        response = client.post("/api/calendar/sync", json={"todos": ["Test todo"]})
    finally:
        app.dependency_overrides.pop(calendar_api.get_calendar_user_token, None)

    assert response.status_code == 200
    assert response.json() == {
        "synced": 1,
        "events": [{"id": "123", "summary": "Test todo"}],
    }
    mock_create.assert_called_once_with("Test todo", {"token": "server-owned"})


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_endpoint_error(mock_create, calendar_user_token_override):
    mock_create.side_effect = CalendarServiceError("Mocked error")
    calendar_user_token_override({"token": "server-owned"})

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Test todo"]},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Mocked error"}


@pytest.mark.parametrize(
    "unsafe_todo",
    [
        "<script>alert('xss')</script>",
        "$(sleep 5)",
    ],
)
@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_rejects_unsafe_todo_text_before_writeback(
    mock_create,
    calendar_user_token_override,
    unsafe_todo,
):
    calendar_user_token_override({"token": "server-owned"})

    response = client.post("/api/calendar/sync", json={"todos": [unsafe_todo]})

    assert response.status_code == 422
    assert response.json() == {"detail": "Unsafe calendar todo text"}
    mock_create.assert_not_called()


@patch("api.calendar.create_calendar_event", new_callable=AsyncMock)
def test_calendar_sync_rejects_mixed_batch_before_any_writeback(
    mock_create,
    calendar_user_token_override,
):
    mock_create.return_value = {"id": "created-before-rejection"}
    calendar_user_token_override({"token": "server-owned"})

    response = client.post(
        "/api/calendar/sync",
        json={"todos": ["Buy milk", "<script>alert('xss')</script>"]},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Unsafe calendar todo text"}
    mock_create.assert_not_called()


def test_calendar_writeback_intent_uses_customer_owned_caldav_account(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="naruon-internal-cache",
                provider="naruon",
                protocol="local",
                owner_id="testuser",
                organization_id="org-acme",
                capabilities=["read"],
                writeback_enabled=False,
            ),
            WritebackSource(
                source_id="calendar-primary",
                provider="fastmail",
                protocol="caldav",
                owner_id="testuser",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="abc123",
            ),
        ]
    )

    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={"action": "create", "summary": "Launch review"},
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


def test_calendar_writeback_update_requires_etag_if_match(writeback_source_override):
    writeback_source_override(
        [
            WritebackSource(
                source_id="calendar-primary",
                provider="fastmail",
                protocol="caldav",
                owner_id="testuser",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="abc123",
            )
        ]
    )

    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={"action": "update", "summary": "Launch review"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["requires_if_match"] is True
    assert data["if_match"] == "abc123"


def test_calendar_writeback_rejects_non_owner_and_naruon_only_storage(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="shared-calendar",
                provider="fastmail",
                protocol="caldav",
                owner_id="other-user",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="abc123",
            )
        ]
    )
    non_owner_response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={"action": "create", "summary": "Launch review"},
    )
    assert non_owner_response.status_code == 422

    writeback_source_override(
        [
            WritebackSource(
                source_id="naruon-cache",
                provider="naruon",
                protocol="local",
                owner_id="testuser",
                organization_id="org-acme",
                capabilities=["read", "write"],
                writeback_enabled=True,
            )
        ]
    )

    naruon_only_response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={"action": "create", "summary": "Launch review"},
    )
    assert naruon_only_response.status_code == 422


def test_calendar_writeback_rejects_targeted_non_owned_source_without_selection(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="shared-calendar",
                provider="fastmail",
                protocol="caldav",
                owner_id="other-user",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="shared-etag",
            ),
            WritebackSource(
                source_id="calendar-primary",
                provider="fastmail",
                protocol="caldav",
                owner_id="testuser",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="owned-etag",
            ),
        ]
    )

    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "target_source_id": "shared-calendar",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Not authorized for requested writeback source"
    }


def test_calendar_writeback_targeted_authorization_hides_source_existence(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="shared-calendar",
                provider="fastmail",
                protocol="caldav",
                owner_id="other-user",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="shared-etag",
            ),
            WritebackSource(
                source_id="cross-org-calendar",
                provider="fastmail",
                protocol="caldav",
                owner_id="testuser",
                organization_id="org-other",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="cross-org-etag",
            )
        ]
    )

    missing_response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "target_source_id": "missing-calendar",
        },
    )
    non_owner_response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "target_source_id": "shared-calendar",
        },
    )
    cross_org_response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "target_source_id": "cross-org-calendar",
        },
    )

    assert missing_response.status_code == 403
    assert non_owner_response.status_code == 403
    assert cross_org_response.status_code == 403
    assert missing_response.json() == non_owner_response.json()
    assert missing_response.json() == cross_org_response.json()


def test_calendar_writeback_allows_org_admin_to_target_same_org_source(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="shared-calendar",
                provider="fastmail",
                protocol="caldav",
                owner_id="other-user",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="shared-etag",
            )
        ]
    )
    org_admin_client = TestClient(
        app,
        headers={
            "X-User-Id": "org-admin",
            "X-User-Role": "tenant_admin",
            "X-Organization-Id": "org-acme",
        },
    )

    response = org_admin_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "target_source_id": "shared-calendar",
        },
    )

    assert response.status_code == 200
    assert response.json()["target_source_id"] == "shared-calendar"


def test_calendar_writeback_allows_system_admin_to_target_any_org_source(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="cross-org-calendar",
                provider="fastmail",
                protocol="caldav",
                owner_id="other-user",
                organization_id="org-other",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="cross-org-etag",
            )
        ]
    )
    system_admin_client = TestClient(
        app,
        headers={"X-User-Id": "platform-ops", "X-User-Role": "system_admin"},
    )

    response = system_admin_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "target_source_id": "cross-org-calendar",
        },
    )

    assert response.status_code == 200
    assert response.json()["target_source_id"] == "cross-org-calendar"


def test_calendar_writeback_selects_owned_source_after_non_owned_candidate(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="shared-calendar",
                provider="fastmail",
                protocol="caldav",
                owner_id="other-user",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="shared-etag",
            ),
            WritebackSource(
                source_id="calendar-primary",
                provider="fastmail",
                protocol="caldav",
                owner_id="testuser",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="owned-etag",
            ),
        ]
    )

    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={"action": "create", "summary": "Launch review"},
    )

    assert response.status_code == 200
    assert response.json()["target_source_id"] == "calendar-primary"


def test_calendar_writeback_rejects_forged_client_source_ownership(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="calendar-primary",
                provider="fastmail",
                protocol="caldav",
                owner_id="testuser",
                organization_id="org-acme",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="abc123",
            )
        ]
    )

    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={
            "action": "create",
            "summary": "Launch review",
            "sources": [
                {
                    "source_id": "attacker-controlled-calendar",
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

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"
    assert response.json()["detail"][0]["loc"] == ["body", "sources"]


def test_calendar_writeback_rejects_same_owner_cross_org_source(
    writeback_source_override,
):
    writeback_source_override(
        [
            WritebackSource(
                source_id="calendar-primary",
                provider="fastmail",
                protocol="caldav",
                owner_id="testuser",
                organization_id="org-other",
                capabilities=["read", "write", "etag"],
                writeback_enabled=True,
                etag="abc123",
            )
        ]
    )

    response = workspace_client.post(
        "/api/calendar/writeback-intent",
        json={"action": "create", "summary": "Launch review"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "No customer-owned writeback source is available"
    }
