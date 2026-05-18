import inspect

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

TEST_DEV_AUTH_TOKEN = (
    "test-dev-auth-token-with-32-byte-minimum"  # noqa: S105 - test-only token
)
WEAK_DEV_AUTH_TOKEN = "weak-token"  # noqa: S105 - test-only token
WRONG_DEV_AUTH_TOKEN = (
    "wrong-dev-auth-token-with-32-byte-min"  # noqa: S105 - test-only token
)
RUNTIME_HEADER_PARAMS = {
    "x_user_id",
    "x_user_role",
    "x_organization_id",
    "x_group_ids",
    "x_dev_auth_token",
}


@pytest.fixture(autouse=True)
def restore_auth_flags():
    previous_debug = settings.DEBUG
    previous_runtime_environment = getattr(settings, "RUNTIME_ENVIRONMENT", None)
    previous_trust = settings.TRUST_DEV_HEADERS
    previous_dev_auth_token = settings.DEV_AUTH_TOKEN
    yield
    settings.DEBUG = previous_debug
    if previous_runtime_environment is not None:
        setattr(settings, "RUNTIME_ENVIRONMENT", previous_runtime_environment)
    settings.TRUST_DEV_HEADERS = previous_trust
    settings.DEV_AUTH_TOKEN = previous_dev_auth_token


def _set_runtime_environment(value: str) -> None:
    if hasattr(settings, "RUNTIME_ENVIRONMENT"):
        setattr(settings, "RUNTIME_ENVIRONMENT", value)


def _enable_local_dev_headers() -> None:
    _set_runtime_environment("local")
    settings.TRUST_DEV_HEADERS = True
    settings.DEV_AUTH_TOKEN = SecretStr(TEST_DEV_AUTH_TOKEN)


def _get_runner_config_without_dependency_overrides(headers: dict[str, str]):
    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            return client.get("/api/runner-config", headers=headers)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)


def _assert_runner_config_rejects_identity_headers(headers: dict[str, str]) -> None:
    response = _get_runner_config_without_dependency_overrides(headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_runtime_auth_dependencies_do_not_declare_dev_header_api_surface():
    auth_context_params = set(inspect.signature(get_auth_context).parameters)
    current_user_params = set(inspect.signature(get_current_user).parameters)

    assert RUNTIME_HEADER_PARAMS.isdisjoint(auth_context_params)
    assert RUNTIME_HEADER_PARAMS.isdisjoint(current_user_params)


@pytest.mark.asyncio
async def test_get_auth_context_rejects_missing_auth():
    # It should raise HTTP 401 when no auth is provided, rather than defaulting to "default".
    with pytest.raises(HTTPException) as exc:
        await get_auth_context()
    assert exc.value.status_code == 401


def test_auth_dependency_overrides_are_opt_in_by_default():
    assert get_auth_context not in app.dependency_overrides
    assert get_current_user not in app.dependency_overrides


@pytest.mark.asyncio
async def test_debug_mode_does_not_trust_unsigned_identity_headers():
    settings.DEBUG = True
    settings.TRUST_DEV_HEADERS = False

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
        }
    )


def test_dev_header_trust_requires_configured_token():
    _set_runtime_environment("local")
    settings.TRUST_DEV_HEADERS = True

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
        }
    )


def test_dev_header_trust_rejects_wrong_token():
    _enable_local_dev_headers()

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
            "X-Dev-Auth-Token": WRONG_DEV_AUTH_TOKEN,
        }
    )


def test_dev_auth_token_does_not_work_when_header_trust_is_disabled():
    _set_runtime_environment("local")
    settings.TRUST_DEV_HEADERS = False
    settings.DEV_AUTH_TOKEN = SecretStr(TEST_DEV_AUTH_TOKEN)

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
            "X-Dev-Auth-Token": TEST_DEV_AUTH_TOKEN,
        }
    )


def test_dev_header_trust_is_rejected_in_production_environment():
    _set_runtime_environment("production")
    settings.TRUST_DEV_HEADERS = True
    settings.DEV_AUTH_TOKEN = SecretStr(TEST_DEV_AUTH_TOKEN)

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
            "X-Dev-Auth-Token": TEST_DEV_AUTH_TOKEN,
        }
    )


def test_dev_header_trust_requires_strong_token():
    _set_runtime_environment("local")
    settings.TRUST_DEV_HEADERS = True
    settings.DEV_AUTH_TOKEN = SecretStr(WEAK_DEV_AUTH_TOKEN)

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
            "X-Dev-Auth-Token": WEAK_DEV_AUTH_TOKEN,
        }
    )


@pytest.mark.asyncio
async def test_runtime_auth_rejects_dev_headers_even_when_local_flags_enabled():
    _enable_local_dev_headers()

    with pytest.raises(HTTPException) as exc:
        await get_auth_context()

    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication required"


def test_http_route_rejects_dev_token_and_forged_role_even_when_flags_enabled():
    _enable_local_dev_headers()

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
            "X-Dev-Auth-Token": TEST_DEV_AUTH_TOKEN,
        }
    )


def test_http_route_rejects_public_identity_headers_without_dev_token():
    settings.TRUST_DEV_HEADERS = False
    settings.DEV_AUTH_TOKEN = None

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "attacker",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-victim",
        }
    )


def test_runtime_auth_rejects_scoped_enterprise_role_headers():
    _enable_local_dev_headers()

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "alice",
            "X-User-Role": "group_admin",
            "X-Organization-Id": "org-acme",
            "X-Group-Ids": "group-1,group-2",
            "X-Dev-Auth-Token": TEST_DEV_AUTH_TOKEN,
        }
    )


def test_runtime_auth_rejects_platform_admin_role_headers():
    _enable_local_dev_headers()

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "root",
            "X-User-Role": "platform_admin",
            "X-Dev-Auth-Token": TEST_DEV_AUTH_TOKEN,
        }
    )


def test_admin_user_id_is_rejected_without_verified_identity_provider():
    _enable_local_dev_headers()

    _assert_runner_config_rejects_identity_headers(
        {
            "X-User-Id": "admin",
            "X-Dev-Auth-Token": TEST_DEV_AUTH_TOKEN,
        }
    )


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
