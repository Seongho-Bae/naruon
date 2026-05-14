import pytest
from fastapi.testclient import TestClient

from core.config import settings
from main import app


@pytest.fixture
def client():
    # Pass default headers for authentication
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c


def test_runtime_config_returns_non_secret_data(client):
    response = client.get("/api/runtime-config")
    assert response.status_code == 200
    data = response.json()
    assert "product_name" in data
    assert "features" in data
    # Ensure no secrets leak
    assert "openai_api_key" not in data
    assert "encryption_key" not in data


def test_runtime_config_exposes_non_secret_auth_capability_flags(client):
    previous_auth_mode = settings.AUTH_MODE
    previous_trust = settings.TRUST_DEV_HEADERS
    previous_secret = settings.OIDC_SHARED_SECRET
    previous_jwks = settings.OIDC_JWKS_URL
    settings.AUTH_MODE = "header"
    settings.TRUST_DEV_HEADERS = True
    settings.OIDC_SHARED_SECRET = None
    settings.OIDC_JWKS_URL = None

    response = client.get("/api/runtime-config")

    settings.AUTH_MODE = previous_auth_mode
    settings.TRUST_DEV_HEADERS = previous_trust
    settings.OIDC_SHARED_SECRET = previous_secret
    settings.OIDC_JWKS_URL = previous_jwks

    assert response.status_code == 200
    data = response.json()
    assert data["features"]["dev_header_auth_enabled"] is True
    assert data["features"]["manual_bearer_login_enabled"] is False


def test_runtime_config_only_enables_manual_bearer_when_full_oidc_validation_inputs_exist(
    client,
):
    previous_auth_mode = settings.AUTH_MODE
    previous_trust = settings.TRUST_DEV_HEADERS
    previous_secret = settings.OIDC_SHARED_SECRET
    previous_jwks = settings.OIDC_JWKS_URL
    previous_issuer = settings.OIDC_ISSUER
    previous_audience = settings.OIDC_AUDIENCE
    settings.AUTH_MODE = "oidc"
    settings.TRUST_DEV_HEADERS = False
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_JWKS_URL = None
    settings.OIDC_ISSUER = None
    settings.OIDC_AUDIENCE = None

    response = client.get("/api/runtime-config")

    settings.AUTH_MODE = previous_auth_mode
    settings.TRUST_DEV_HEADERS = previous_trust
    settings.OIDC_SHARED_SECRET = previous_secret
    settings.OIDC_JWKS_URL = previous_jwks
    settings.OIDC_ISSUER = previous_issuer
    settings.OIDC_AUDIENCE = previous_audience

    assert response.status_code == 200
    assert response.json()["features"]["manual_bearer_login_enabled"] is False
