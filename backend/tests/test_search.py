import datetime
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from db.session import get_db


class MockRow:
    def __init__(self, id, subject, sender, content, score):
        self.id = id
        self.subject = subject
        self.sender = sender
        self.content = content
        self.score = score
        self.date = datetime.datetime(2026, 4, 27, 10, 0, tzinfo=datetime.timezone.utc)
        self.thread_id = "thread-123"
        self.reply_count = 2


class MockResult:
    def all(self):
        return [MockRow(1, "Test Subject", "test@test.com", "Test Body", 1.0)]


class MockTenantConfig:
    def __init__(self):
        self.openai_api_key = "test-key"

class MockSession:
    async def execute(self, stmt):
        return MockResult()
    
    async def scalar(self, stmt):
        return MockTenantConfig()


async def override_get_db():
    yield MockSession()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@patch("api.search.generate_embeddings", new_callable=AsyncMock)
def test_search_endpoint_success(mock_generate_embeddings, client):
    mock_generate_embeddings.return_value = [[0.1] * 1536]

    response = client.post("/api/search", json={"query": "test query"})
    if response.status_code != 200:
        import traceback

        traceback.print_exc()
        print(response.json())

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == 1
    assert data["results"][0]["subject"] == "Test Subject"
    assert data["results"][0]["date"] == "2026-04-27T10:00:00Z"
    assert data["results"][0]["thread_id"] == "thread-123"
    assert data["results"][0]["reply_count"] == 2


def test_search_reply_counts_group_by_coalesced_thread_key():
    from api.search import build_reply_counts_subquery

    subquery = build_reply_counts_subquery()
    sql = str(subquery.select()).lower()

    assert "coalesce(nullif(btrim(btrim(emails.thread_id)" in sql
    assert "nullif(btrim(btrim(emails.message_id)" in sql
    assert "coalesce(emails.thread_id, emails.message_id)" not in sql
    assert "count(emails.id)" in sql
    assert "group by coalesce(nullif(btrim(btrim(emails.thread_id)" in sql
