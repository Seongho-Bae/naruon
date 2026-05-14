import pytest

from core.config import settings


@pytest.fixture(autouse=True)
def enable_trusted_header_auth_for_repo_tests():
    previous_auth_mode = settings.AUTH_MODE
    previous_trust = settings.TRUST_DEV_HEADERS
    settings.AUTH_MODE = "header"
    settings.TRUST_DEV_HEADERS = True
    yield
    settings.AUTH_MODE = previous_auth_mode
    settings.TRUST_DEV_HEADERS = previous_trust
