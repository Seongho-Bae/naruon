from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import SecretStr

from core.config import settings
from db.session import get_db
from main import app

from tests.test_network_api import get_override

client = TestClient(app)


def test_network_graph_rejects_attacker_controlled_user_header(monkeypatch, real_auth):
    monkeypatch.setattr(
        settings, "API_AUTH_TOKEN", SecretStr("expected-token"), raising=False
    )

    with patch.dict(app.dependency_overrides, {get_db: get_override([])}):
        response = client.get(
            "/api/network/graph",
            headers={"X-User-Id": "attacker-selected-user"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
