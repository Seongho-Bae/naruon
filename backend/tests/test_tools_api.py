import base64
import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient

from main import app


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _signed_session_token() -> str:
    header_segment = _base64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    payload_segment = _base64url_encode(
        json.dumps(
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
    )
    signing_input = f"{header_segment}.{payload_segment}"
    signature = hmac.new(
        os.environ["AUTH_SESSION_HMAC_SECRET"].encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def test_tools_rejects_missing_signed_session():
    with TestClient(app) as client:
        response = client.get("/api/tools")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_get_tools_returns_valid_data():
    with TestClient(app) as client:
        response = client.get(
            "/api/tools",
            headers={"Authorization": f"Bearer {_signed_session_token()}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

    first_tool = data[0]
    assert "name" in first_tool
    assert "description" in first_tool
    assert "category" in first_tool
    assert first_tool["category"] == "이메일 분석"
