import json
import hmac
import hashlib
import base64
import datetime
import inspect

import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jwt.algorithms import RSAAlgorithm
from api.auth import (
    AuthContext,
    ensure_organization_access,
    get_auth_context,
    get_current_user,
)
from core.config import settings


@pytest.fixture(autouse=True)
def restore_auth_flags():
    previous_debug = settings.DEBUG
    previous_trust = settings.TRUST_DEV_HEADERS
    previous_auth_mode = settings.AUTH_MODE
    previous_jwt_secret = getattr(settings, "OIDC_SHARED_SECRET", None)
    previous_issuer = getattr(settings, "OIDC_ISSUER", None)
    previous_audience = getattr(settings, "OIDC_AUDIENCE", None)
    previous_jwks_url = getattr(settings, "OIDC_JWKS_URL", None)
    yield
    settings.DEBUG = previous_debug
    settings.TRUST_DEV_HEADERS = previous_trust
    settings.AUTH_MODE = previous_auth_mode
    settings.OIDC_SHARED_SECRET = previous_jwt_secret
    settings.OIDC_ISSUER = previous_issuer
    settings.OIDC_AUDIENCE = previous_audience
    settings.OIDC_JWKS_URL = previous_jwks_url


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _encode_test_jwt(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_part = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64url(signature)}"


def _build_test_jwk(public_key, kid: str) -> dict:
    jwk = json.loads(RSAAlgorithm.to_jwk(public_key))
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return jwk


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_auth():
    with pytest.raises(HTTPException) as exc:
        await get_current_user()
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_supports_scoped_enterprise_roles_from_bearer_claims():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"

    token = _encode_test_jwt(
        {
            "sub": "alice",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "organization_id": "org-acme",
            "groups": ["group-1", "group-2"],
            "roles": ["group_admin"],
        },
        settings.OIDC_SHARED_SECRET,
    )

    context = await get_auth_context(authorization=f"Bearer {token}")

    assert context == AuthContext(
        user_id="alice",
        role="group_admin",
        organization_id="org-acme",
        group_ids=("group-1", "group-2"),
        workspace_id="workspace-org-acme",
    )


@pytest.mark.asyncio
async def test_get_auth_context_keeps_workspace_fallback_for_unscoped_bearer_claims():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"

    token = _encode_test_jwt(
        {
            "sub": "root",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "roles": ["platform_admin"],
        },
        settings.OIDC_SHARED_SECRET,
    )

    context = await get_auth_context(authorization=f"Bearer {token}")

    assert context.role == "platform_admin"
    assert context.organization_id is None
    assert context.group_ids == ()
    assert context.workspace_id == "workspace-root"


def test_ensure_organization_access_rejects_cross_scope_resource():
    context = AuthContext(
        user_id="alice",
        role="organization_admin",
        organization_id="org-acme",
        group_ids=("group-1",),
        workspace_id="workspace-org-acme",
    )

    with pytest.raises(HTTPException) as exc:
        ensure_organization_access(context, "org-other")

    assert exc.value.status_code == 403
    assert exc.value.detail == "Resource belongs to a different organization"


@pytest.mark.asyncio
async def test_get_auth_context_accepts_valid_bearer_token_claims():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"

    token = _encode_test_jwt(
        {
            "sub": "alice",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "organization_id": "org-acme",
            "groups": ["group-1", "group-2"],
            "roles": ["organization_admin"],
        },
        settings.OIDC_SHARED_SECRET,
    )

    context = await get_auth_context(authorization=f"Bearer {token}")

    assert context == AuthContext(
        user_id="alice",
        role="organization_admin",
        organization_id="org-acme",
        group_ids=("group-1", "group-2"),
        workspace_id="workspace-org-acme",
    )


@pytest.mark.asyncio
async def test_get_auth_context_does_not_promote_admin_subject_without_role_claims():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"

    token = _encode_test_jwt(
        {
            "sub": "admin",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "organization_id": "org-acme",
        },
        settings.OIDC_SHARED_SECRET,
    )

    context = await get_auth_context(authorization=f"Bearer {token}")

    assert context.role == "member"


@pytest.mark.asyncio
async def test_get_auth_context_accepts_valid_jwks_bearer_token_claims(monkeypatch):
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = None
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"
    settings.OIDC_JWKS_URL = (
        "https://issuer.example.com/realms/naruon/protocol/openid-connect/certs"
    )

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = "test-key-1"
    token = jwt.encode(
        {
            "sub": "oidc-admin",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "organization_id": "org-acme",
            "roles": ["organization_admin"],
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )

    def fake_fetch_data(_self):
        return {"keys": [_build_test_jwk(private_key.public_key(), kid)]}

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", fake_fetch_data)

    context = await get_auth_context(authorization=f"Bearer {token}")

    assert context == AuthContext(
        user_id="oidc-admin",
        role="organization_admin",
        organization_id="org-acme",
        group_ids=(),
        workspace_id="workspace-org-acme",
    )


@pytest.mark.asyncio
async def test_get_auth_context_uses_async_boundary_for_jwks_lookup(monkeypatch):
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = None
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"
    settings.OIDC_JWKS_URL = (
        "https://issuer.example.com/realms/naruon/protocol/openid-connect/certs"
    )

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = "test-key-async"
    token = jwt.encode(
        {
            "sub": "oidc-admin",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "organization_id": "org-acme",
            "roles": ["organization_admin"],
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )

    def fake_fetch_data(_self):
        return {"keys": [_build_test_jwk(private_key.public_key(), kid)]}

    to_thread_called = {"value": False}

    async def fake_to_thread(func, *args, **kwargs):
        to_thread_called["value"] = True
        return func(*args, **kwargs)

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", fake_fetch_data)
    monkeypatch.setattr("api.auth.asyncio.to_thread", fake_to_thread)

    context = await get_auth_context(authorization=f"Bearer {token}")

    assert context.user_id == "oidc-admin"
    assert to_thread_called["value"] is True


@pytest.mark.asyncio
async def test_get_auth_context_reuses_cached_jwks_client(monkeypatch):
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = None
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"
    settings.OIDC_JWKS_URL = (
        "https://issuer.example.com/realms/naruon/protocol/openid-connect/certs"
    )

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = "test-key-cache"
    token = jwt.encode(
        {
            "sub": "oidc-admin",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "organization_id": "org-acme",
            "roles": ["organization_admin"],
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )

    def fake_fetch_data(_self):
        return {"keys": [_build_test_jwk(private_key.public_key(), kid)]}

    original_client = jwt.PyJWKClient
    constructor_calls = {"count": 0}

    class CountingPyJWKClient(original_client):
        def __init__(self, uri, *args, **kwargs):
            constructor_calls["count"] += 1
            super().__init__(uri, *args, **kwargs)

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", fake_fetch_data)
    monkeypatch.setattr("api.auth.jwt.PyJWKClient", CountingPyJWKClient)
    from api.auth import _get_jwk_client

    _get_jwk_client.cache_clear()

    await get_auth_context(authorization=f"Bearer {token}")
    await get_auth_context(authorization=f"Bearer {token}")

    assert constructor_calls["count"] == 1


@pytest.mark.asyncio
async def test_get_auth_context_rejects_invalid_bearer_signature():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"

    token = _encode_test_jwt(
        {
            "sub": "mallory",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "organization_id": "org-acme",
            "roles": ["platform_admin"],
        },
        "wrong-secret",
    )

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(authorization=f"Bearer {token}")

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_rejects_dev_headers_when_not_trusted():
    settings.DEBUG = False
    settings.TRUST_DEV_HEADERS = False
    settings.AUTH_MODE = "hybrid"

    with pytest.raises(HTTPException) as exc:
        await get_auth_context()

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_rejects_dev_headers_even_when_trusted_flag_is_set():
    settings.DEBUG = False
    settings.TRUST_DEV_HEADERS = True
    settings.AUTH_MODE = "hybrid"

    signature = inspect.signature(get_auth_context)
    assert "x_user_id" not in signature.parameters
    assert "x_user_role" not in signature.parameters
    assert "x_organization_id" not in signature.parameters
    assert "x_group_ids" not in signature.parameters

    with pytest.raises(HTTPException) as exc:
        await get_auth_context()

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_rejects_dev_headers_even_when_debug_is_enabled():
    settings.DEBUG = True
    settings.TRUST_DEV_HEADERS = False
    settings.AUTH_MODE = "hybrid"

    signature = inspect.signature(get_current_user)
    assert "x_user_id" not in signature.parameters
    assert "x_user_role" not in signature.parameters
    assert "x_organization_id" not in signature.parameters
    assert "x_group_ids" not in signature.parameters

    with pytest.raises(HTTPException) as exc:
        await get_current_user()

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_rejects_header_mode_when_headers_are_not_trusted():
    settings.DEBUG = False
    settings.TRUST_DEV_HEADERS = False
    settings.AUTH_MODE = "header"

    with pytest.raises(HTTPException) as exc:
        await get_auth_context()

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_rejects_header_mode_even_when_trusted_flag_is_set():
    settings.DEBUG = False
    settings.TRUST_DEV_HEADERS = True
    settings.AUTH_MODE = "header"

    with pytest.raises(HTTPException) as exc:
        await get_auth_context()

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_rejects_bearer_token_without_expiration():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"

    token = _encode_test_jwt(
        {
            "sub": "alice",
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "organization_id": "org-acme",
            "roles": ["organization_admin"],
        },
        settings.OIDC_SHARED_SECRET,
    )

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(authorization=f"Bearer {token}")

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_rejects_bearer_token_without_configured_issuer():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = None
    settings.OIDC_AUDIENCE = "naruon-web"

    token = _encode_test_jwt(
        {
            "sub": "alice",
            "iss": "https://issuer.example.com/realms/naruon",
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
        },
        settings.OIDC_SHARED_SECRET,
    )

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(authorization=f"Bearer {token}")

    assert exc.value.status_code == 503
    assert exc.value.detail == "OIDC issuer and audience are not configured"


@pytest.mark.asyncio
async def test_get_auth_context_rejects_bearer_token_without_configured_audience():
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = None

    token = _encode_test_jwt(
        {
            "sub": "alice",
            "iss": settings.OIDC_ISSUER,
            "aud": "naruon-web",
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
        },
        settings.OIDC_SHARED_SECRET,
    )

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(authorization=f"Bearer {token}")

    assert exc.value.status_code == 503
    assert exc.value.detail == "OIDC issuer and audience are not configured"
