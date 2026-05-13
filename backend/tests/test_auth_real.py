import pytest
from fastapi import HTTPException
from api.auth import AuthContext, ensure_organization_access, get_auth_context, get_current_user
from core.config import settings


@pytest.fixture(autouse=True)
def restore_auth_flags():
    previous_debug = settings.DEBUG
    previous_trust = settings.TRUST_DEV_HEADERS
    yield
    settings.DEBUG = previous_debug
    settings.TRUST_DEV_HEADERS = previous_trust

@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_auth():
    # It should raise HTTP 401 when no auth is provided, rather than defaulting to "default".
    with pytest.raises(HTTPException) as exc:
        await get_current_user(x_user_id=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_auth_context_supports_scoped_enterprise_roles():
    settings.TRUST_DEV_HEADERS = True

    context = await get_auth_context(
        x_user_id="alice",
        x_user_role="group_admin",
        x_organization_id="org-acme",
        x_group_ids="group-1,group-2",
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

    context = await get_auth_context(
        x_user_id="root",
        x_user_role="platform_admin",
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
