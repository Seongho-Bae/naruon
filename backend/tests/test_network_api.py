from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from db.session import get_db
from main import app
from tests.conftest import TEST_AUTH_HEADERS


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


async def get_network_response(path: str, rows, headers: dict[str, str] | None = None):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=TEST_AUTH_HEADERS,
    ) as client:
        with patch.dict(app.dependency_overrides, {get_db: get_override(rows)}):
            return await client.get(path, headers=headers)


@pytest.mark.asyncio
async def test_network_endpoint_exists():
    response = await get_network_response(
        "/api/network/graph",
        [
            ("alice@example.com", "bob@example.com, charlie@example.com"),
            ("bob@example.com", "alice@example.com"),
            ("alice@example.com", "bob@example.com"),
        ],
    )

    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data

    nodes = {node["id"] for node in data["nodes"]}
    assert "alice@example.com" in nodes
    assert "bob@example.com" in nodes
    assert "charlie@example.com" in nodes

    edges = {
        (edge["source"], edge["target"]): edge.get("weight", 1)
        for edge in data["edges"]
    }
    assert edges[("alice@example.com", "bob@example.com")] == 2
    assert edges[("alice@example.com", "charlie@example.com")] == 1
    assert edges[("bob@example.com", "alice@example.com")] == 1


@pytest.mark.asyncio
async def test_network_endpoint_empty_db():
    response = await get_network_response("/api/network/graph", [])

    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 0
    assert len(data["edges"]) == 0


@pytest.mark.asyncio
async def test_network_endpoint_none_recipients():
    response = await get_network_response(
        "/api/network/graph",
        [
            ("alice@example.com", None),
            ("bob@example.com", ""),
        ],
    )

    assert response.status_code == 200
    data = response.json()
    nodes = {node["id"] for node in data["nodes"]}
    assert "alice@example.com" in nodes
    assert "bob@example.com" in nodes
    assert len(data["edges"]) == 0


@pytest.mark.asyncio
async def test_network_endpoint_malformed_emails():
    response = await get_network_response(
        "/api/network/graph",
        [
            ("not_an_email", "bob@example.com, also_not_an_email"),
            ("alice@example.com", "malformed@@@example.com"),
        ],
    )

    assert response.status_code == 200
    data = response.json()
    nodes = {node["id"] for node in data["nodes"]}
    assert "not_an_email" not in nodes
    assert "also_not_an_email" not in nodes
    assert "malformed@@@example.com" not in nodes
    assert "alice@example.com" in nodes
    assert "bob@example.com" in nodes
    assert len(data["edges"]) == 0


@pytest.mark.asyncio
async def test_network_endpoint_query_params():
    response = await get_network_response(
        "/api/network/graph?limit=10&user_id=default",
        [("alice@example.com", "bob@example.com")],
        headers={**TEST_AUTH_HEADERS, "X-User-Id": "attacker"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


@pytest.mark.asyncio
async def test_network_endpoint_rejects_user_id_impersonation():
    response = await get_network_response(
        "/api/network/graph?user_id=attacker",
        [("alice@example.com", "bob@example.com")],
        headers={**TEST_AUTH_HEADERS, "X-User-Id": "attacker"},
    )

    assert response.status_code == 403
