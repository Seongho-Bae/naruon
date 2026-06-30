import pytest
from fastapi import HTTPException
from tests.conftest import _parse_group_ids, _derive_test_role, _derive_workspace_id, _normalize_header_value

def test_parse_group_ids_empty():
    assert _parse_group_ids("") == ()

def test_derive_test_role_invalid():
    assert _derive_test_role("invalid_role") == "member"

def test_derive_workspace_id_no_org():
    assert _derive_workspace_id("user1", None) == "workspace-user1"

def test_dev_auth_dependency_overrides_unauth(dev_auth_dependency_overrides):
    from main import app
    from api.auth import get_auth_context
    import asyncio

    test_auth_context = app.dependency_overrides[get_auth_context]

    with pytest.raises(HTTPException) as exc:
        asyncio.run(test_auth_context(x_user_id=None, x_user_role=None, x_organization_id=None, x_group_ids=None))

    assert exc.value.status_code == 401

def test_dev_auth_dependency_overrides_auth(dev_auth_dependency_overrides):
    from main import app
    from api.auth import get_auth_context, get_current_user
    import asyncio

    test_auth_context = app.dependency_overrides[get_auth_context]
    test_current_user = app.dependency_overrides[get_current_user]

    auth_ctx = asyncio.run(test_auth_context(x_user_id="user_1", x_user_role=None, x_organization_id=None, x_group_ids=None))
    assert auth_ctx.user_id == "user_1"

    user_id = asyncio.run(test_current_user(x_user_id="user_1", x_user_role=None, x_organization_id=None, x_group_ids=None))
    assert user_id == "user_1"

def test_normalize_header_value():
    assert _normalize_header_value(None) is None
    assert _normalize_header_value("  ") is None
    assert _normalize_header_value(" val ") == "val"

def test_parse_group_ids():
    assert _parse_group_ids(" group1 , group2 ") == ("group1", "group2")

def test_derive_test_role():
    assert _derive_test_role("system_admin") == "system_admin"

def test_derive_workspace_id_org():
    assert _derive_workspace_id("user1", "org1") == "workspace-org1"

def test_dev_auth_dependency_overrides_cleanup():
    import tests.conftest as mod
    from main import app
    from api.auth import get_auth_context, get_current_user

    # We call the underlying generator
    gen = mod.dev_auth_dependency_overrides.__wrapped__()
    next(gen)

    assert get_auth_context in app.dependency_overrides
    assert get_current_user in app.dependency_overrides

    try:
        next(gen)
    except StopIteration:
        pass

    assert get_auth_context not in app.dependency_overrides
    assert get_current_user not in app.dependency_overrides
