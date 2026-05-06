from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from db.session import get_db
from main import app
from tests.conftest import TEST_AUTH_HEADERS


class MockTenantConfig:
    def __init__(self):
        self.openai_api_key = "test-key"


class MockSession:
    async def scalar(self, stmt):
        return MockTenantConfig()


@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        yield MockSession()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=TEST_AUTH_HEADERS,
    ) as c:
        yield c
    app.dependency_overrides.clear()


@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
@patch("api.llm.draft_reply", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_llm_endpoints_exist(mock_draft, mock_extract, client: AsyncClient):
    from services.llm_service import ExtractionResult

    mock_extract.return_value = ExtractionResult(
        summary="Test summary", todos=["Task 1"]
    )
    mock_draft.return_value = "This is a draft reply."

    resp1 = await client.post("/api/llm/summarize", json={"email_body": "test"})
    resp2 = await client.post(
        "/api/llm/draft", json={"email_body": "test", "instruction": "reply yes"}
    )

    assert resp1.status_code == 200
    assert resp2.status_code == 200


@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_summarize_endpoint(mock_extract, client: AsyncClient):
    from services.llm_service import ExtractionResult

    mock_extract.return_value = ExtractionResult(
        summary="Test summary", todos=["Task 1"]
    )

    resp = await client.post("/api/llm/summarize", json={"email_body": "test email"})
    assert resp.status_code == 200
    assert resp.json() == {"summary": "Test summary", "todos": ["Task 1"]}


@patch("api.llm.draft_reply", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_draft_endpoint(mock_draft, client: AsyncClient):
    mock_draft.return_value = "This is a draft reply."

    resp = await client.post(
        "/api/llm/draft",
        json={"email_body": "test email", "instruction": "reply nicely"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"draft": "This is a draft reply."}
