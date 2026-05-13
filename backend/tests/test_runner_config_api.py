from fastapi.testclient import TestClient
import pytest

from core.config import settings
from db.models import WorkspaceRunnerConfig
from db.session import get_db
from main import app


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

    def add(self, obj):
        if isinstance(obj, WorkspaceRunnerConfig):
            obj.id = 1
            self.runner = obj

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


@pytest.fixture
def mock_db():
    return MockAsyncSession()


@pytest.fixture(autouse=True)
def enable_dev_headers():
    previous = settings.TRUST_DEV_HEADERS
    settings.TRUST_DEV_HEADERS = True
    yield
    settings.TRUST_DEV_HEADERS = previous


@pytest.fixture
def member_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"}) as c:
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
                "X-User-Role": "organization_admin",
                "X-Organization-Id": "org-acme",
            },
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def second_org_admin_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "org-admin-2",
                "X-User-Role": "organization_admin",
                "X-Organization-Id": "org-acme",
            },
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def platform_admin_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "platform-root",
                "X-User-Role": "platform_admin",
                "X-Organization-Id": "org-acme",
            },
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_member_cannot_manage_runner_config(member_client):
    response = member_client.get("/api/runner-config")
    assert response.status_code == 403

    response = member_client.post("/api/runner-config/rotate")
    assert response.status_code == 403


def test_org_scoped_runner_config_uses_shared_workspace(admin_client, second_org_admin_client):
    rotate_response = admin_client.post("/api/runner-config/rotate")
    assert rotate_response.status_code == 200
    rotate_data = rotate_response.json()
    assert rotate_data["workspace_id"] == "workspace-org-acme"
    assert rotate_data["registration_token"].startswith("nrn_")

    read_response = second_org_admin_client.get("/api/runner-config")
    assert read_response.status_code == 200
    read_data = read_response.json()
    assert read_data["workspace_id"] == "workspace-org-acme"
    assert read_data["configured"] is True
    assert read_data["fingerprint"] is not None
    assert "registration_token" not in read_data


def test_platform_admin_can_manage_runner_config(platform_admin_client):
    rotate_response = platform_admin_client.post("/api/runner-config/rotate")
    assert rotate_response.status_code == 200
    assert rotate_response.json()["workspace_id"] == "workspace-org-acme"


def test_org_admin_without_org_scope_is_rejected(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "admin",
                "X-User-Role": "organization_admin",
            },
        ) as client:
            response = client.get("/api/runner-config")
            assert response.status_code == 403
            assert response.json()["detail"] == "Organization scope is required"
    finally:
        app.dependency_overrides.pop(get_db, None)
