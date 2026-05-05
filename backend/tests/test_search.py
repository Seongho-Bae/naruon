import datetime
import inspect
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app
from db.session import get_db
from tests.conftest import TEST_AUTH_HEADERS


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
    def __init__(self):
        self.scalar_params = []

    async def execute(self, stmt):
        return MockResult()
    
    async def scalar(self, stmt):
        self.scalar_params.append(stmt.compile().params)
        return MockTenantConfig()


async def override_get_db():
    yield MockSession()


@pytest.fixture
def mock_session():
    return MockSession()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers=TEST_AUTH_HEADERS) as c:
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


@patch("api.search.generate_embeddings", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_search_uses_authenticated_user_not_x_user_id_header(mock_generate_embeddings, mock_session):
    from api.auth import get_current_user
    from api.search import SearchRequest, hybrid_search

    mock_generate_embeddings.return_value = [[0.1] * 1536]

    response = await hybrid_search(
        SearchRequest(query="test query"),
        db=mock_session,
        current_user="default",
    )

    assert "x_user_id" not in inspect.signature(get_current_user).parameters
    assert len(response.results) == 1
    assert mock_session.scalar_params[0]["user_id_1"] == "default"


@patch("api.search.generate_embeddings", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_search_rejects_user_id_impersonation_with_authenticated_user(
    mock_generate_embeddings, mock_session
):
    from fastapi import HTTPException
    from api.search import SearchRequest, hybrid_search

    mock_generate_embeddings.return_value = [[0.1] * 1536]

    with pytest.raises(HTTPException) as exc_info:
        await hybrid_search(
            SearchRequest(query="test query"),
            user_id="attacker",
            db=mock_session,
            current_user="default",
        )

    assert exc_info.value.status_code == 403


@patch("api.search.generate_embeddings", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_search_escapes_snippet_content_before_response(mock_generate_embeddings):
    from api.search import SearchRequest, hybrid_search

    mock_generate_embeddings.return_value = [[0.1] * 1536]

    class XssMockResult(MockResult):
        def all(self):
            return [
                MockRow(
                    1,
                    "Test Subject",
                    "test@test.com",
                    '<script>alert("x")</script>&',
                    1.0,
                )
            ]

    class XssMockSession(MockSession):
        async def execute(self, stmt):
            return XssMockResult()

    response = await hybrid_search(
        SearchRequest(query="test query"),
        db=cast(Any, XssMockSession()),
        current_user="default",
    )

    snippet = response.results[0].snippet
    assert "<script>" not in snippet
    assert snippet == "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;&amp;"


def test_search_request_normalizes_whitespace_before_use():
    from api.search import SearchRequest

    request = SearchRequest(query="  quarterly\n   roadmap\t  ")

    assert request.query == "quarterly roadmap"


def test_search_request_rejects_control_characters_before_use():
    from api.search import SearchRequest

    with pytest.raises(ValidationError):
        SearchRequest(query="invoice\x00 OR 1=1")


def test_search_request_rejects_overlong_queries_before_use():
    from api.search import SearchRequest

    with pytest.raises(ValidationError):
        SearchRequest(query="a" * 513)


def test_search_reply_counts_group_by_coalesced_thread_key():
    from api.search import build_reply_counts_subquery

    subquery = build_reply_counts_subquery()
    sql = str(subquery.select()).lower()

    assert "coalesce(nullif(btrim(btrim(emails.thread_id)" in sql
    assert "nullif(btrim(btrim(emails.message_id)" in sql
    assert "coalesce(emails.thread_id, emails.message_id)" not in sql
    assert "count(emails.id)" in sql
    assert "group by coalesce(nullif(btrim(btrim(emails.thread_id)" in sql
