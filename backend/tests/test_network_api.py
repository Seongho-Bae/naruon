import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

client = TestClient(app)

class MockResult:
    def fetchall(self):
        return [
            ("alice@example.com", "bob@example.com, charlie@example.com"),
            ("bob@example.com", "alice@example.com"),
            ("alice@example.com", "bob@example.com")
        ]

class MockSession:
    async def execute(self, query):
        return MockResult()

async def override_get_db():
    yield MockSession()

def test_network_endpoint_exists():
    old_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    
    try:
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
    finally:
        if old_override:
            app.dependency_overrides[get_db] = old_override
        else:
            app.dependency_overrides.pop(get_db, None)
