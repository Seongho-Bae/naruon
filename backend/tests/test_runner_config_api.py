import base64
import datetime
import hashlib
import hmac
import json

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
def configure_oidc_auth():
    previous_auth_mode = settings.AUTH_MODE
    previous_secret = settings.OIDC_SHARED_SECRET
    previous_issuer = settings.OIDC_ISSUER
    previous_audience = settings.OIDC_AUDIENCE
    previous_trust = settings.TRUST_DEV_HEADERS
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"
    settings.TRUST_DEV_HEADERS = False
    yield
    settings.AUTH_MODE = previous_auth_mode
    settings.OIDC_SHARED_SECRET = previous_secret
    settings.OIDC_ISSUER = previous_issuer
    settings.OIDC_AUDIENCE = previous_audience
    settings.TRUST_DEV_HEADERS = previous_trust


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _encode_test_jwt(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_part = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64url(signature)}"


def _auth_headers(
    user_id: str, role: str, organization_id: str | None = "org-acme"
) -> dict[str, str]:
    secret = settings.OIDC_SHARED_SECRET
    assert secret is not None
    token = _encode_test_jwt(
        {
            "sub": user_id,
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "roles": [role],
            **({"organization_id": organization_id} if organization_id else {}),
        },
        secret,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, headers=_auth_headers("testuser", "member")) as c:
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
            headers=_auth_headers("admin", "organization_admin"),
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
            headers=_auth_headers("org-admin-2", "organization_admin"),
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
            headers=_auth_headers("platform-root", "platform_admin"),
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_member_cannot_manage_runner_config(member_client):
    response = member_client.get("/api/runner-config")
    assert response.status_code == 403

    response = member_client.post("/api/runner-config/rotate")
    assert response.status_code == 403


def test_org_scoped_runner_config_uses_shared_workspace(
    admin_client, second_org_admin_client, mock_db
):
    rotate_response = admin_client.post("/api/runner-config/rotate")
    assert rotate_response.status_code == 200
    rotate_data = rotate_response.json()
    assert rotate_data["workspace_id"] == "workspace-org-acme"
    assert rotate_data["registration_token"].startswith("nrn_")
    assert mock_db.runner.organization_id == "org-acme"

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
            headers=_auth_headers("admin", "organization_admin", organization_id=None),
        ) as client:
            response = client.get("/api/runner-config")
            assert response.status_code == 403
            assert response.json()["detail"] == "Organization scope is required"
    finally:
        app.dependency_overrides.pop(get_db, None)
