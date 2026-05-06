import os

import pytest
from pydantic import SecretStr

from core.auth_tokens import create_signed_auth_token

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
)
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key")

from core.config import settings


TEST_AUTH_USER_ID = "default"
TEST_AUTH_SIGNING_SECRET = "test-auth-signing-secret-with-at-least-32-bytes"
TEST_AUTH_TOKEN = create_signed_auth_token(TEST_AUTH_USER_ID, TEST_AUTH_SIGNING_SECRET)
TEST_AUTH_HEADERS = {"Authorization": f"Bearer {TEST_AUTH_TOKEN}"}


@pytest.fixture(autouse=True)
def configure_api_auth(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_USER_ID", TEST_AUTH_USER_ID)
    monkeypatch.setattr(
        settings,
        "API_AUTH_SIGNING_SECRET",
        SecretStr(TEST_AUTH_SIGNING_SECRET),
        raising=False,
    )
    monkeypatch.setattr(settings, "API_AUTH_SIGNING_SECRET_FILE", None, raising=False)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return dict(TEST_AUTH_HEADERS)
