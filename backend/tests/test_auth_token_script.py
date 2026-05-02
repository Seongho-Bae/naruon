import os
import subprocess
import sys
from pathlib import Path

import pytest
import jwt

from api.auth import get_current_user


@pytest.mark.asyncio
async def test_create_auth_token_script_emits_backend_accepted_token(monkeypatch):
    secret = "test-auth-secret-with-at-least-32-bytes"
    env = {**os.environ, "AUTH_TOKEN_SECRET": secret}
    script_path = Path(__file__).parents[2] / "scripts" / "create_auth_token.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "alice"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    monkeypatch.setenv("AUTH_TOKEN_SECRET", secret)
    token = result.stdout.strip()
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    assert token.count(".") == 2
    assert payload["jti"]
    assert await get_current_user(f"Bearer {token}") == "alice"
