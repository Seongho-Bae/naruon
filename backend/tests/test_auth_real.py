import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr
from api.auth import (
    AuthContext,
    ensure_organization_access,
    get_auth_context,
    get_current_user,
)
from core.config import settings
from main import app


@pytest.fixture(autouse=True)
def restore_auth_flags():
    previous_debug = settings.DEBUG
    previous_trust = settings.TRUST_DEV_HEADERS
    previous_dev_auth_token = settings.DEV_AUTH_TOKEN
    yield
    settings.DEBUG = previous_debug
    settings.TRUST_DEV_HEADERS = previous_trust
    settings.DEV_AUTH_TOKEN = previous_dev_auth_token


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_auth():
    # It should raise HTTP 401 when no auth is provided, rather than defaulting to "default".
    with pytest.raises(HTTPException) as exc:
        await get_current_user(x_user_id=None)
    assert exc.value.status_code == 401


def test_auth_dependency_overrides_are_opt_in_by_default():
    assert get_auth_context not in app.dependency_overrides
    assert get_current_user not in app.dependency_overrides


@pytest.mark.asyncio
async def test_debug_mode_does_not_trust_unsigned_identity_headers():
    settings.DEBUG = True
    settings.TRUST_DEV_HEADERS = False

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(
            x_user_id="attacker",
            x_user_role="platform_admin",
            x_organization_id="org-victim",
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication required"


@pytest.mark.asyncio
async def test_dev_header_trust_requires_configured_token():
    settings.TRUST_DEV_HEADERS = True

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(
            x_user_id="attacker",
            x_user_role="platform_admin",
            x_organization_id="org-victim",
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication required"


@pytest.mark.asyncio
async def test_dev_header_trust_rejects_wrong_token():
    settings.TRUST_DEV_HEADERS = True
    settings.DEV_AUTH_TOKEN = SecretStr("expected-dev-auth-token")

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(
            x_user_id="attacker",
            x_user_role="platform_admin",
            x_organization_id="org-victim",
            x_dev_auth_token="wrong-dev-auth-token",
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication required"


@pytest.mark.asyncio
async def test_dev_auth_token_does_not_work_when_header_trust_is_disabled():
    settings.TRUST_DEV_HEADERS = False
    settings.DEV_AUTH_TOKEN = SecretStr("expected-dev-auth-token")

    with pytest.raises(HTTPException) as exc:
        await get_auth_context(
            x_user_id="attacker",
            x_user_role="platform_admin",
            x_organization_id="org-victim",
            x_dev_auth_token="expected-dev-auth-token",
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication required"


def test_http_route_rejects_public_identity_headers_without_dev_token():
    settings.TRUST_DEV_HEADERS = False
    settings.DEV_AUTH_TOKEN = None
    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)

    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "attacker",
                "X-User-Role": "platform_admin",
                "X-Organization-Id": "org-victim",
            },
        ) as client:
            response = client.get("/api/runner-config")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


@pytest.mark.asyncio
async def test_get_auth_context_supports_scoped_enterprise_roles():
    settings.TRUST_DEV_HEADERS = True
    settings.DEV_AUTH_TOKEN = SecretStr("test-dev-auth-token")

    context = await get_auth_context(
        x_user_id="alice",
        x_user_role="group_admin",
        x_organization_id="org-acme",
        x_group_ids="group-1,group-2",
        x_dev_auth_token="test-dev-auth-token",
    )

    assert context == AuthContext(
        user_id="alice",
        role="group_admin",
        organization_id="org-acme",
        group_ids=("group-1", "group-2"),
        workspace_id="workspace-org-acme",
    )


@pytest.mark.asyncio
async def test_get_auth_context_keeps_legacy_workspace_fallback_for_unscoped_dev_auth():
    settings.TRUST_DEV_HEADERS = True
    settings.DEV_AUTH_TOKEN = SecretStr("test-dev-auth-token")

    context = await get_auth_context(
        x_user_id="root",
        x_user_role="platform_admin",
        x_dev_auth_token="test-dev-auth-token",
    )

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
