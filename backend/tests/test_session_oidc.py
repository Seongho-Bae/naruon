import pytest
from fastapi.testclient import TestClient
from core.config import settings
from main import app
from pydantic import SecretStr
import jwt

@pytest.fixture
def mock_jwks_client(monkeypatch):
    class MockKey:
        key_id = "test-key"
        key = "test-secret"

    class MockJWKSClient:
        def get_signing_key_from_jwt(self, token):
            return MockKey()

    client = MockJWKSClient()
    import api.auth
    monkeypatch.setattr(api.auth, "jwks_client", client)
    return client

@pytest.mark.asyncio
async def test_oidc_exchange_endpoint(monkeypatch, mock_jwks_client):
    settings.OIDC_ISSUER_URL = "https://login.example.test"
    settings.OIDC_CLIENT_ID = "naruon-api"
    settings.OIDC_JWKS_URL = "https://login.example.test/jwks"
    settings.AUTH_SESSION_HMAC_SECRET = SecretStr("0123456789abcdefABCDEF!@#$%12345678")

    def mock_decode(*args, **kwargs):
         return {
            "sub": "alice",
            "role": "member",
            "org": "org-acme",
            "groups": ["group-1"],
            "workspace": "workspace-1",
            "exp": 9999999999,
            "iss": "https://login.example.test",
            "aud": "naruon-api"
        }
    import jwt as real_jwt
    monkeypatch.setattr(real_jwt, "decode", mock_decode)

    client = TestClient(app)
    response = client.post(
        "/api/auth/session/oidc-exchange",
        json={"id_token": "mocked.token.string"}
    )

    assert response.status_code == 200
    assert "naruon_session" in response.json()

    token = response.json()["naruon_session"]

    # decode the HMAC session token
    decoded = jwt.decode(
        token,
        settings.AUTH_SESSION_HMAC_SECRET.get_secret_value().encode("utf-8"),
        algorithms=["HS256"],
        audience="naruon-control-plane",
        issuer="naruon-control-plane"
    )

    assert decoded["sub"] == "alice"
    assert decoded["role"] == "member"
    assert decoded["org"] == "org-acme"
    assert decoded["workspace"] == "workspace-1"
