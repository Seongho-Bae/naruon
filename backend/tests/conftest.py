import os

import pytest
from pydantic import SecretStr

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
)
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key")

from core.config import settings


TEST_AUTH_USER_ID = "default"
TEST_AUTH_TOKEN = "test-token"
TEST_AUTH_HEADERS = {"Authorization": f"Bearer {TEST_AUTH_TOKEN}"}


@pytest.fixture(autouse=True)
def configure_api_auth(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_USER_ID", TEST_AUTH_USER_ID)
    monkeypatch.setattr(settings, "API_AUTH_BEARER_TOKEN", SecretStr(TEST_AUTH_TOKEN))
    monkeypatch.setattr(settings, "API_AUTH_BEARER_TOKEN_FILE", None)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return dict(TEST_AUTH_HEADERS)
