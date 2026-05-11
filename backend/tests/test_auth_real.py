import pytest
from fastapi import HTTPException
from api.auth import get_current_user

@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_auth():
    # It should raise HTTP 401 when no auth is provided, rather than defaulting to "default".
    with pytest.raises(HTTPException) as exc:
        await get_current_user(x_user_id=None)
    assert exc.value.status_code == 401
