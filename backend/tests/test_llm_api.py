import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from db.session import get_db


class MockTenantConfig:
    def __init__(self, openai_api_key="test-key"):
        self.openai_api_key = openai_api_key


class MockSession:
    def __init__(self, tenant_config=None):
        self.tenant_config = tenant_config or MockTenantConfig()

    async def scalar(self, stmt):
        return self.tenant_config


@pytest.fixture
def client():
    async def override_get_db():
        yield MockSession()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()


@pytest.fixture
def client_without_openai_key():
    async def override_get_db():
        yield MockSession(MockTenantConfig(openai_api_key=""))

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()


@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_llm_endpoints_exist(mock_draft, mock_extract, client):
    from services.llm_service import ExtractionResult

    mock_extract.return_value = ExtractionResult(
        summary="Test summary", todos=["Task 1"]
    )
    mock_draft.return_value = "This is a draft reply."

    resp1 = client.post("/api/llm/summarize", json={"email_body": "test"})
    resp2 = client.post(
        "/api/llm/draft", json={"email_body": "test", "instruction": "reply yes"}
    )

    assert resp1.status_code == 200
    assert resp2.status_code == 200


@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
def test_summarize_endpoint(mock_extract, client):
    from services.llm_service import ExtractionResult

    mock_extract.return_value = ExtractionResult(
        summary="Test summary", todos=["Task 1"]
    )

    resp = client.post("/api/llm/summarize", json={"email_body": "test email"})
    assert resp.status_code == 200
    assert resp.json() == {"summary": "Test summary", "todos": ["Task 1"]}


@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_draft_endpoint(mock_draft, client):
    mock_draft.return_value = "This is a draft reply."

    resp = client.post(
        "/api/llm/draft",
        json={"email_body": "test email", "instruction": "reply nicely"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"draft": "This is a draft reply."}


def test_summarize_missing_openai_key_returns_config_error(client_without_openai_key):
    response = client_without_openai_key.post(
        "/api/llm/summarize", json={"email_body": "test email"}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "OpenAI API key not configured"}


def test_draft_missing_openai_key_returns_config_error(client_without_openai_key):
    response = client_without_openai_key.post(
        "/api/llm/draft",
        json={"email_body": "test email", "instruction": "reply nicely"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "OpenAI API key not configured"}
