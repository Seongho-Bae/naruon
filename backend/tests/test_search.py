import datetime
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


class MockRow:
    def __init__(self, id, subject, sender, content, score):
        self.id = id
        self.source_message_id = "<test@example.com>"
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


class MockTenantConfigResult:
    def __init__(self, config):
        self.config = config

    def scalar_one_or_none(self):
        return self.config


class MockTenantConfig:
    def __init__(self):
        self.openai_api_key = "test-key"


class MockSession:
    async def execute(self, stmt):
        if "tenant_configs" in str(stmt).lower():
            return MockTenantConfigResult(MockTenantConfig())
        return MockResult()

    async def scalar(self, stmt):
        return MockTenantConfig()


async def override_get_db():
    yield MockSession()


class CapturingMockSession(MockSession):
    def __init__(self):
        self.statements = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        return await super().execute(stmt)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
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
    assert data["results"][0]["source_message_id"] == "<test@example.com>"
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


@patch("api.search.generate_embeddings", new_callable=AsyncMock)
def test_search_endpoint_query_is_scoped_to_current_user(mock_generate_embeddings):
    mock_generate_embeddings.return_value = [[0.1] * 1536]
    session = CapturingMockSession()

    async def override_scoped_db():
        yield session

    app.dependency_overrides[get_db] = override_scoped_db
    try:
        with TestClient(
            app,
            headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
        ) as client:
            response = client.post("/api/search", json={"query": "test query"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    query_text = str(session.statements[-1]).lower()
    assert "emails.user_id" in query_text
    assert "emails.organization_id" in query_text
    query_params = session.statements[-1].compile().params
    user_scope_params = {
        value for key, value in query_params.items() if key.startswith("user_id")
    }
    organization_scope_params = {
        value
        for key, value in query_params.items()
        if key.startswith("organization_id")
    }
    assert user_scope_params == {"testuser"}
    assert organization_scope_params == {"org-acme"}
