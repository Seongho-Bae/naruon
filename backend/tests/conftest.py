import pytest

from api.auth import get_current_user
from main import app

_MISSING = object()


@pytest.fixture(autouse=True)
def default_authenticated_user():
    previous_override = app.dependency_overrides.get(get_current_user, _MISSING)

    async def override_get_current_user() -> str:
        return "test_user"

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    if previous_override is _MISSING:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = previous_override
