import pytest
from fastapi import Header
from pydantic import SecretStr

from api.auth import AuthContext, build_auth_context, get_auth_context, get_current_user
from core.config import settings
from main import app

TEST_DEV_AUTH_TOKEN = (
    "test-dev-auth-token-with-32-byte-minimum"  # noqa: S105 - test-only token
)


@pytest.fixture
def dev_auth_dependency_overrides():
    previous_runtime_environment = settings.RUNTIME_ENVIRONMENT
    previous_trust = settings.TRUST_DEV_HEADERS
    previous_dev_auth_token = settings.DEV_AUTH_TOKEN
    settings.RUNTIME_ENVIRONMENT = "test"
    settings.TRUST_DEV_HEADERS = True
    settings.DEV_AUTH_TOKEN = SecretStr(TEST_DEV_AUTH_TOKEN)

    async def test_auth_context(
        x_user_id: str | None = Header(None, alias="X-User-Id"),
        x_user_role: str | None = Header(None, alias="X-User-Role"),
        x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
        x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
    ) -> AuthContext:
        return build_auth_context(
            x_user_id=x_user_id,
            x_user_role=x_user_role,
            x_organization_id=x_organization_id,
            x_group_ids=x_group_ids,
            x_dev_auth_token=TEST_DEV_AUTH_TOKEN,
        )

    async def test_current_user(
        x_user_id: str | None = Header(None, alias="X-User-Id"),
        x_user_role: str | None = Header(None, alias="X-User-Role"),
        x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
        x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
    ) -> str:
        return (
            await test_auth_context(
                x_user_id=x_user_id,
                x_user_role=x_user_role,
                x_organization_id=x_organization_id,
                x_group_ids=x_group_ids,
            )
        ).user_id

    app.dependency_overrides[get_auth_context] = test_auth_context
    app.dependency_overrides[get_current_user] = test_current_user
    yield
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)
    settings.RUNTIME_ENVIRONMENT = previous_runtime_environment
    settings.TRUST_DEV_HEADERS = previous_trust
    settings.DEV_AUTH_TOKEN = previous_dev_auth_token
