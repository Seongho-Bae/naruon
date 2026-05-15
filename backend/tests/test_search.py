import datetime
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from db.session import get_db
from tests.auth_helpers import auth_headers


class MockRow:
    def __init__(self, id, subject, sender, content, score):
        self.id = id
        self.mailbox_account_id = 2
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
    def __init__(self, mailbox_account_ids=None):
        self.mailbox_account_ids = set(mailbox_account_ids or {1, 2, 3})

    async def execute(self, stmt):
        return MockResult()

    async def scalar(self, stmt):
        query_text = str(stmt).lower()
        if "from mailbox_accounts" in query_text:
            params = stmt.compile().params
            mailbox_account_id = next(
                (value for key, value in params.items() if "id" in key),
                None,
            )
            return (
                mailbox_account_id
                if mailbox_account_id in self.mailbox_account_ids
                else None
            )
        return MockTenantConfig()


class MailboxScopedMockSession(MockSession):
    async def execute(self, stmt):
        params = stmt.compile().params
        mailbox_account_id = next(
            (value for key, value in params.items() if "mailbox_account_id" in key),
            None,
        )
        if mailbox_account_id == 2:
            return MockResult()
        return type("EmptyResult", (), {"all": lambda self: []})()


async def override_get_db():
    yield MockSession()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers=auth_headers("testuser")) as c:
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
    assert data["results"][0]["mailbox_account_id"] == 2
    assert data["results"][0]["date"] == "2026-04-27T10:00:00Z"
    assert data["results"][0]["thread_id"] == "thread-123"
    assert data["results"][0]["reply_count"] == 2


@patch("api.search.generate_embeddings", new_callable=AsyncMock)
def test_search_endpoint_filters_by_mailbox_account_id(mock_generate_embeddings):
    async def scoped_db():
        yield MailboxScopedMockSession()

    app.dependency_overrides[get_db] = scoped_db
    mock_generate_embeddings.return_value = [[0.1] * 1536]

    try:
        with TestClient(app, headers=auth_headers("testuser")) as client:
            allowed = client.post(
                "/api/search", json={"query": "test query", "mailbox_account_id": 2}
            )
            blocked = client.post(
                "/api/search", json={"query": "test query", "mailbox_account_id": 1}
            )
    finally:
        app.dependency_overrides.clear()

    assert allowed.status_code == 200
    assert len(allowed.json()["results"]) == 1
    assert blocked.status_code == 200
    assert blocked.json()["results"] == []


@patch("api.search.generate_embeddings", new_callable=AsyncMock)
def test_search_endpoint_rejects_unowned_mailbox_account_id(
    mock_generate_embeddings,
):
    async def scoped_db():
        yield MockSession(mailbox_account_ids={2})

    app.dependency_overrides[get_db] = scoped_db
    mock_generate_embeddings.return_value = [[0.1] * 1536]

    try:
        with TestClient(app, headers=auth_headers("testuser")) as client:
            response = client.post(
                "/api/search", json={"query": "test query", "mailbox_account_id": 1}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Mailbox account not found"}
    mock_generate_embeddings.assert_not_called()


def test_search_reply_counts_group_by_coalesced_thread_key():
    from api.search import build_reply_counts_subquery

    subquery = build_reply_counts_subquery("testuser")
    sql = str(subquery.select()).lower()

    assert "coalesce(nullif(btrim(btrim(emails.thread_id)" in sql
    assert "nullif(btrim(btrim(emails.message_id)" in sql
    assert "coalesce(emails.thread_id, emails.message_id)" not in sql
    assert "count(emails.id)" in sql
    assert "group by coalesce(nullif(btrim(btrim(emails.thread_id)" in sql


def test_mailbox_scoped_search_keeps_legacy_null_mailbox_thread_context():
    from api.search import build_reply_counts_subquery

    subquery = build_reply_counts_subquery("testuser", mailbox_account_id=2)
    sql = str(subquery.select()).lower()

    assert "emails.mailbox_account_id" in sql
    assert "emails.mailbox_account_id is null" in sql
