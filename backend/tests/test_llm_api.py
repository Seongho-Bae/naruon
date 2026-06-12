import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from db.models import LLMProvider
from main import app
from db.session import get_db
from services.llm_provider_selection import LOCAL_PROVIDER_API_KEY

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


class MockTenantConfig:
    def __init__(self, openai_api_key="test-key"):
        self.openai_api_key = openai_api_key


class MockTenantConfigResult:
    def __init__(self, tenant_config):
        self.tenant_config = tenant_config

    def scalar_one_or_none(self):
        return self.tenant_config


class MockScalars:
    def __init__(self, items):
        self.items = items

    def first(self):
        return self.items[0] if self.items else None


class MockProviderResult:
    def __init__(self, providers):
        self.providers = providers

    def scalars(self):
        return MockScalars(self.providers)


class MockSession:
    def __init__(self, tenant_config=None, providers=None):
        self.tenant_config = tenant_config or MockTenantConfig()
        self.providers = providers or []

    async def execute(self, stmt):
        if "llm_providers" in str(stmt).lower():
            return MockProviderResult(self.providers)
        return MockTenantConfigResult(self.tenant_config)

    async def scalar(self, stmt):
        return self.tenant_config


@pytest.fixture
def client():
    async def override_get_db():
        yield MockSession()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c
    app.dependency_overrides.clear()


@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_llm_endpoints_exist(mock_draft, mock_extract, client):
    from services.llm_service import ExtractionResult

    mock_extract.return_value = ExtractionResult(
        summary="Test summary", todos=["Task 1"], provenance="OpenAI", confidence=90
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
        summary="Test summary", todos=["Task 1"], provenance="OpenAI", confidence=90
    )

    resp = client.post("/api/llm/summarize", json={"email_body": "test email"})
    assert resp.status_code == 200
    assert resp.json() == {
        "summary": "Test summary",
        "todos": ["Task 1"],
        "provenance": "OpenAI",
        "confidence": 90,
    }


@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_draft_endpoint(mock_draft, client):
    mock_draft.return_value = "This is a draft reply."

    resp = client.post(
        "/api/llm/draft",
        json={"email_body": "test email", "instruction": "reply nicely"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"draft": "This is a draft reply."}


@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_draft_endpoint_uses_active_local_model_provider(mock_draft):
    provider = LLMProvider(
        id=7,
        user_id="admin",
        organization_id="org-acme",
        name="Local Gemma4",
        provider_type="ollama",
        base_url="http://ollama:11434/v1",
        model_identifier="gemma4",
        embedding_model="embeddinggemma",
        api_key=None,
        is_active=True,
    )
    mock_draft.return_value = "Gemma4 draft"

    async def override_get_db():
        yield MockSession(
            tenant_config=MockTenantConfig(openai_api_key=None),
            providers=[provider],
        )

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "testuser",
                "X-Organization-Id": "org-acme",
            },
        ) as test_client:
            resp = test_client.post(
                "/api/llm/draft",
                json={"email_body": "test email", "instruction": "reply nicely"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"draft": "Gemma4 draft"}
    mock_draft.assert_awaited_once_with(
        "test email",
        "reply nicely",
        LOCAL_PROVIDER_API_KEY,
        base_url="http://ollama:11434/v1",
        model="gemma4",
    )


def test_llm_endpoints_preserve_missing_key_400():
    async def override_get_db():
        yield MockSession(MockTenantConfig(openai_api_key=None))

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, headers={"X-User-Id": "testuser"}) as test_client:
            summarize = test_client.post(
                "/api/llm/summarize", json={"email_body": "test email"}
            )
            draft = test_client.post(
                "/api/llm/draft",
                json={"email_body": "test email", "instruction": "reply nicely"},
            )
    finally:
        app.dependency_overrides.clear()

    assert summarize.status_code == 400
    assert summarize.json() == {"detail": "OpenAI API key not configured"}
    assert draft.status_code == 400
    assert draft.json() == {"detail": "OpenAI API key not configured"}
