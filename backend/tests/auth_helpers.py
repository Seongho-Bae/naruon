import datetime

import jwt

from core.config import settings

TEST_AUTH_AUDIENCE = "naruon-web"
TEST_AUTH_ISSUER = "https://issuer.example.com/realms/naruon"
TEST_AUTH_SECRET = "test-secret"


def configure_test_auth() -> None:
    settings.AUTH_MODE = "hybrid"
    settings.TRUST_DEV_HEADERS = False
    settings.OIDC_SHARED_SECRET = TEST_AUTH_SECRET
    settings.OIDC_ISSUER = TEST_AUTH_ISSUER
    settings.OIDC_AUDIENCE = TEST_AUTH_AUDIENCE
    settings.OIDC_JWKS_URL = None


def auth_headers(
    user_id: str = "testuser",
    role: str = "member",
    organization_id: str | None = None,
    group_ids: tuple[str, ...] = (),
) -> dict[str, str]:
    payload: dict[str, object] = {
        "sub": user_id,
        "iss": TEST_AUTH_ISSUER,
        "aud": TEST_AUTH_AUDIENCE,
        "exp": int(
            (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(minutes=5)
            ).timestamp()
        ),
        "roles": [role],
    }
    if organization_id is not None:
        payload["organization_id"] = organization_id
    if group_ids:
        payload["groups"] = list(group_ids)
    token = jwt.encode(payload, TEST_AUTH_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
