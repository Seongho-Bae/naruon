import base64
import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient
from main import app
from db.session import get_db
from unittest.mock import patch

client = TestClient(app)


class MockResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class MockSession:
    def __init__(self, rows):
        self.rows = rows
        self.executed_sql = []

    async def execute(self, query):
        self.executed_sql.append(str(query).lower())
        return MockResult(self.rows)


def get_override(rows):
    async def override_get_db():
        yield MockSession(rows)

    return override_get_db


def signed_bearer_token(user_id: str, secret: str = "test-auth-secret") -> str:
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + 3600},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    encoded_payload = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(
        secret.encode(), encoded_payload.encode(), hashlib.sha256
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"Bearer {encoded_payload}.{encoded_signature}"


def test_network_endpoint_exists():
    with patch.dict(
        app.dependency_overrides,
        {
            get_db: get_override(
                [
                    ("alice@example.com", "bob@example.com, charlie@example.com"),
                    ("bob@example.com", "alice@example.com"),
                    ("alice@example.com", "bob@example.com"),
                ]
            )
        },
    ):
        response = client.get("/api/network/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

        nodes = {n["id"] for n in data["nodes"]}
        assert "alice@example.com" in nodes
        assert "bob@example.com" in nodes
        assert "charlie@example.com" in nodes

        edges = {(e["source"], e["target"]): e.get("weight", 1) for e in data["edges"]}
        assert edges[("alice@example.com", "bob@example.com")] == 2
        assert edges[("alice@example.com", "charlie@example.com")] == 1
        assert edges[("bob@example.com", "alice@example.com")] == 1


def test_network_endpoint_empty_db():
    with patch.dict(app.dependency_overrides, {get_db: get_override([])}):
        response = client.get("/api/network/graph")
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 0
        assert len(data["edges"]) == 0


def test_network_endpoint_none_recipients():
    with patch.dict(
        app.dependency_overrides,
        {
            get_db: get_override(
                [
                    ("alice@example.com", None),
                    ("bob@example.com", ""),
                ]
            )
        },
    ):
        response = client.get("/api/network/graph")
        assert response.status_code == 200
        data = response.json()
        nodes = {n["id"] for n in data["nodes"]}
        assert "alice@example.com" in nodes
        assert "bob@example.com" in nodes
        assert len(data["edges"]) == 0


def test_network_endpoint_malformed_emails():
    with patch.dict(
        app.dependency_overrides,
        {
            get_db: get_override(
                [
                    ("not_an_email", "bob@example.com, also_not_an_email"),
                    ("alice@example.com", "malformed@@@example.com"),
                ]
            )
        },
    ):
        response = client.get("/api/network/graph")
        assert response.status_code == 200
        data = response.json()
        nodes = {n["id"] for n in data["nodes"]}
        assert "not_an_email" not in nodes
        assert "also_not_an_email" not in nodes
        assert "malformed@@@example.com" not in nodes

        assert "alice@example.com" in nodes
        assert "bob@example.com" in nodes

        assert len(data["edges"]) == 0


def test_network_endpoint_query_params():
    with patch.dict(
        app.dependency_overrides,
        {
            get_db: get_override(
                [
                    ("alice@example.com", "bob@example.com"),
                ]
            )
        },
    ):
        response = client.get("/api/network/graph?limit=10&user_id=test_user")
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1


def test_network_endpoint_rejects_excessive_limit_before_query():
    session = MockSession([("alice@example.com", "bob@example.com")])

    async def override_get_db():
        yield session

    with patch.dict(app.dependency_overrides, {get_db: override_get_db}):
        response = client.get("/api/network/graph?limit=999999999")

    assert response.status_code == 422
    assert session.executed_sql == []


def test_network_endpoint_filters_graph_query_by_current_user():
    session = MockSession([("alice@example.com", "bob@example.com")])

    async def override_get_db():
        yield session

    with patch.dict(app.dependency_overrides, {get_db: override_get_db}):
        response = client.get("/api/network/graph", headers={"X-User-Id": "alice"})

    assert response.status_code == 200
    assert any("emails.user_id" in sql for sql in session.executed_sql)


def test_network_endpoint_rejects_forged_x_user_id_without_signed_bearer_token():
    session = MockSession([("victim@example.com", "attacker@example.com")])

    async def override_get_db():
        yield session

    with patch.dict(app.dependency_overrides, {get_db: override_get_db}, clear=True):
        response = client.get("/api/network/graph", headers={"X-User-Id": "victim"})

    assert response.status_code == 401
    assert session.executed_sql == []


def test_network_endpoint_uses_signed_token_not_x_user_id_for_authorization():
    session = MockSession([("alice@example.com", "bob@example.com")])

    async def override_get_db():
        yield session

    with patch.dict(
        app.dependency_overrides, {get_db: override_get_db}, clear=True
    ), patch.dict("os.environ", {"AUTH_TOKEN_SECRET": "test-auth-secret"}):
        response = client.get(
            "/api/network/graph?user_id=bob",
            headers={
                "Authorization": signed_bearer_token("alice"),
                "X-User-Id": "bob",
            },
        )

    assert response.status_code == 403
    assert session.executed_sql == []
