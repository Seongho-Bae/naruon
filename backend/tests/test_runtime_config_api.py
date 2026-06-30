import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _signed_session_token() -> str:
    header_bytes = json.dumps(
        {"alg": "HS256", "typ": "JWT"},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    payload_bytes = json.dumps(
        {
            "ver": 1,
            "iss": "naruon-control-plane",
            "aud": "naruon-api",
            "sub": "alice",
            "role": "member",
            "org": "org-acme",
            "groups": ["group-1"],
            "workspace": "workspace-org-acme",
            "exp": int(time.time()) + 300,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    header_segment = _base64url_encode(header_bytes)
    payload_segment = _base64url_encode(payload_bytes)
    signing_input = f"{header_segment}.{payload_segment}"
    signature = hmac.new(
        os.environ["AUTH_SESSION_HMAC_SECRET"].encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def test_runtime_config_rejects_missing_signed_session(client):
    response = client.get("/api/runtime-config")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_runtime_config_returns_non_secret_data(client):
    response = client.get(
        "/api/runtime-config",
        headers={"Authorization": f"Bearer {_signed_session_token()}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "product_name" in data
    assert "features" in data
    # Ensure no secrets leak
    assert "openai_api_key" not in data
    assert "encryption_key" not in data


@pytest.mark.asyncio
async def test_get_runtime_config_direct():
    from api.runtime_config import RuntimeConfigResponse, get_runtime_config

    response = await get_runtime_config()
    assert isinstance(response, RuntimeConfigResponse)
    assert response.product_name == "Naruon"
    expected_version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert response.version == expected_version
    assert response.features == {
        "llm_enabled": True,
        "smtp_enabled": True,
        "imap_enabled": True,
    }
