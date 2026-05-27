from fastapi.testclient import TestClient
import pytest

from api import runner_ws
from core.config import settings
from db.models import WorkspaceRunnerConfig
from db.session import get_db
from main import app

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


class MockResult:
    def __init__(self, obj):
        self.obj = obj

    def scalar_one_or_none(self):
        return self.obj


class MockAsyncSession:
    def __init__(self):
        self.runner = None

    async def execute(self, query):
        return MockResult(self.runner)


@pytest.fixture(autouse=True)
def reset_runner_connections():
    runner_ws.manager.reset()
    yield
    runner_ws.manager.reset()


@pytest.fixture
def mock_db():
    return MockAsyncSession()


@pytest.fixture
def member_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app, headers={"X-User-Id": "member", "X-Organization-Id": "org-acme"}
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def admin_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "admin",
                "X-User-Role": "tenant_admin",
                "X-Organization-Id": "org-acme",
            },
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_member_cannot_read_operational_signals(member_client):
    response = member_client.get("/api/observability/operational-signals")

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "ORG_ADMIN_REQUIRED"


def test_admin_without_org_scope_gets_deterministic_error(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "admin",
                "X-User-Role": "tenant_admin",
            },
        ) as client:
            response = client.get("/api/observability/operational-signals")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "ORG_SCOPE_REQUIRED"


def test_operational_signals_are_truthful_when_unconfigured(admin_client):
    response = admin_client.get("/api/observability/operational-signals")

    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == "workspace-org-acme"
    assert data["audit_event"] == "observability.operational_signals.viewed"
    assert data["telemetry"] == {
        "prometheus_metrics_enabled": False,
        "otel_traces_enabled": False,
        "otel_endpoint_configured": False,
        "otel_endpoint_host": None,
    }
    assert data["connector"]["registration_state"] == "not_registered"
    assert data["connector"]["connection_state"] == "not_connected"
    assert data["connector"]["active_connection_count"] == 0
    assert data["connector"]["last_heartbeat_at"] is None
    assert data["connector"]["queue_depth_state"] == "not_reported"
    assert data["connector"]["control_plane_domain"] == "naruon.net"
    signals = {signal["signal_key"]: signal for signal in data["signals"]}
    assert signals["prometheus_metrics"]["state"] == "not_configured"
    assert signals["otel_traces"]["state"] == "not_configured"
    assert signals["connector_heartbeat"]["state"] == "not_registered"
    assert signals["sync_lag"]["state"] == "instrumentation_pending"
    assert signals["writeback_conflicts"]["state"] == "intent_only"
    assert all(signal["provider_write_executed"] is False for signal in data["signals"])


def test_operational_signals_reflect_registered_connector_and_otel(
    admin_client, mock_db, monkeypatch
):
    previous_metrics = settings.ENABLE_PROMETHEUS_METRICS
    settings.ENABLE_PROMETHEUS_METRICS = True
    monkeypatch.setenv("ENABLE_OTEL", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    mock_db.runner = WorkspaceRunnerConfig(
        organization_id="org-acme",
        workspace_id="workspace-org-acme",
        registration_token="nrn_registered-token",
    )
    runner_ws.manager.connection_records["org-acme:token-fingerprint"] = (
        runner_ws.RunnerConnectionRecord(
            organization_id="org-acme",
            workspace_id="workspace-org-acme",
            connected_at="2026-05-27T12:00:00Z",
        )
    )
    try:
        response = admin_client.get("/api/observability/operational-signals")
    finally:
        settings.ENABLE_PROMETHEUS_METRICS = previous_metrics

    assert response.status_code == 200
    data = response.json()
    assert data["telemetry"]["prometheus_metrics_enabled"] is True
    assert data["telemetry"]["otel_traces_enabled"] is True
    assert data["telemetry"]["otel_endpoint_host"] == "otel-collector:4317"
    assert data["connector"]["registration_state"] == "registration_configured"
    assert data["connector"]["connection_state"] == "connected"
    assert data["connector"]["active_connection_count"] == 1
    assert data["connector"]["last_heartbeat_at"] == "2026-05-27T12:00:00Z"
    assert "nrn_registered-token" not in str(data)
    signals = {signal["signal_key"]: signal for signal in data["signals"]}
    assert signals["prometheus_metrics"]["state"] == "enabled"
    assert signals["otel_traces"]["state"] == "enabled"
    assert signals["connector_heartbeat"]["state"] == "enabled"
