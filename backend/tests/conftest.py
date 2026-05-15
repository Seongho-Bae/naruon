import pytest

from core.config import settings
from tests.auth_helpers import configure_test_auth


@pytest.fixture(autouse=True)
def enable_bearer_auth_for_repo_tests():
    previous_auth_mode = settings.AUTH_MODE
    previous_trust = settings.TRUST_DEV_HEADERS
    previous_secret = settings.OIDC_SHARED_SECRET
    previous_issuer = settings.OIDC_ISSUER
    previous_audience = settings.OIDC_AUDIENCE
    previous_jwks_url = settings.OIDC_JWKS_URL
    configure_test_auth()
    yield
    settings.AUTH_MODE = previous_auth_mode
    settings.TRUST_DEV_HEADERS = previous_trust
    settings.OIDC_SHARED_SECRET = previous_secret
    settings.OIDC_ISSUER = previous_issuer
    settings.OIDC_AUDIENCE = previous_audience
    settings.OIDC_JWKS_URL = previous_jwks_url
