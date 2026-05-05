import pytest
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

    async def execute(self, query):
        return MockResult(self.rows)


def get_override(rows):
    async def override_get_db():
        yield MockSession(rows)

    return override_get_db


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
        response = client.get("/api/network/graph?limit=10&user_id=default", headers={"X-User-Id": "attacker"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1


def test_network_endpoint_rejects_user_id_impersonation():
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
        response = client.get("/api/network/graph?user_id=attacker", headers={"X-User-Id": "attacker"})

        assert response.status_code == 403
