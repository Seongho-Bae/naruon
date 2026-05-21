import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from core.config import settings
from main import app
from db.models import PromptTemplate
from db.session import get_db

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


class MockSession:
    def __init__(self):
        self.items = []

    async def execute(self, stmt):
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return self.items

                    def first(self):
                        return self.items[0] if self.items else None

                m = MockScalars()
                m.items = getattr(self, "items", self.parent_items)
                return m

        res = MockResult()
        res.parent_items = self.items
        return res

    def add(self, obj):
        import datetime

        if isinstance(obj, PromptTemplate):
            obj.id = len(self.items) + 1
            obj.created_at = datetime.datetime.now(datetime.timezone.utc)
            obj.updated_at = datetime.datetime.now(datetime.timezone.utc)
            self.items.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


mock_session = MockSession()


@pytest.fixture(autouse=True)
def override_get_db():
    app.dependency_overrides[get_db] = lambda: mock_session
    yield
    app.dependency_overrides.clear()
    mock_session.items = []


@pytest.fixture
def auth_client():
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c


def test_prompt_crud(auth_client):
    # Create
    resp = auth_client.post(
        "/api/prompts",
        json={
            "title": "Test Prompt",
            "description": "A test prompt",
            "content": "Summarize this: {{email}}",
            "is_shared": False,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "Test Prompt"

    # List
    resp = auth_client.get("/api/prompts")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_prompt_test_execution_mocked(auth_client, monkeypatch):
    import api.prompts as prompts_module

    # Mock LLM service
    async def mock_execute(*args, **kwargs):
        return {"result": "Mocked LLM result"}

    monkeypatch.setattr(prompts_module, "execute_prompt_with_llm", mock_execute)

    # Mock the db to have a provider
    from db.models import LLMProvider

    p = LLMProvider(
        id=1, name="Test", provider_type="openai", api_key="test-key", is_active=True
    )
    mock_session.items.append(p)

    resp = auth_client.post(
        "/api/prompts/test",
        json={
            "content": "Summarize this: {{email}}",
            "variables": {"email": "hello world"},
        },
    )

    assert resp.status_code == 200
    assert resp.json()["result"] == "Mocked LLM result"


@pytest.mark.asyncio
async def test_execute_prompt_with_llm_disables_redirect_following_for_custom_base_url(
    monkeypatch,
):
    from api.prompts import execute_prompt_with_llm

    monkeypatch.setattr(
        settings, "ALLOWED_LLM_BASE_URL_HOSTS", "llm-gateway.example.com"
    )

    def fake_getaddrinfo(host, port, type=0):
        assert host == "llm-gateway.example.com"
        assert port == 443
        return [(2, 1, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(
        "services.llm_provider_urls.socket.getaddrinfo", fake_getaddrinfo
    )

    with patch("openai.AsyncOpenAI") as mock_async_openai:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Prompt result"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_async_openai.return_value = mock_client

        result = await execute_prompt_with_llm(
            "Summarize this",
            "test-key",
            base_url="https://llm-gateway.example.com/v1",
        )

    assert result == {"result": "Prompt result"}
    constructor_kwargs = mock_async_openai.call_args.kwargs
    assert "http_client" in constructor_kwargs
    assert constructor_kwargs["http_client"].follow_redirects is False
    await constructor_kwargs["http_client"].aclose()
    mock_client.close.assert_awaited_once()
