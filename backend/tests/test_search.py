import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

client = TestClient(app)

class MockEmail:
    def __init__(self, id, subject, sender, body):
        self.id = id
        self.subject = subject
        self.sender = sender
        self.body = body

class MockRow:
    def __init__(self, email, score):
        self.Email = email
        self.score = score

class MockResult:
    def all(self):
        return [
            MockRow(MockEmail(1, "Test Subject", "test@test.com", "Test Body"), 1.0)
        ]

class MockSession:
    async def execute(self, stmt):
        return MockResult()

async def override_get_db():
    yield MockSession()

app.dependency_overrides[get_db] = override_get_db

@patch("api.search.generate_embeddings", new_callable=AsyncMock)
def test_search_endpoint_success(mock_generate_embeddings):
    mock_generate_embeddings.return_value = [[0.1] * 1536]
    
    response = client.post("/api/search", json={"query": "test query"})
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == 1
    assert data["results"][0]["subject"] == "Test Subject"