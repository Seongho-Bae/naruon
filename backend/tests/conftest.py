import os

import pytest

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
)
os.environ.setdefault("ENCRYPTION_KEY", "test-only-local-encryption-key")

from api.auth import get_current_user
from main import app


@pytest.fixture
def real_auth():
    """Opt out of the default authenticated API test principal."""


@pytest.fixture(autouse=True)
def authenticated_api_principal(request):
    if "real_auth" in request.fixturenames:
        yield
        return

    app.dependency_overrides[get_current_user] = lambda: "default"
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
