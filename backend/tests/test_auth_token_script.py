import os
import subprocess
import sys
from pathlib import Path

import pytest

from api.auth import get_current_user


@pytest.mark.asyncio
async def test_create_auth_token_script_emits_backend_accepted_token(monkeypatch):
    secret = "test-auth-secret"
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
    assert await get_current_user(f"Bearer {token}") == "alice"
