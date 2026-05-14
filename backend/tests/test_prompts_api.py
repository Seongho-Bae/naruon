import pytest
from fastapi.testclient import TestClient
from main import app
from db.models import LLMProvider, PromptTemplate, TenantConfig
from db.session import get_db
from api.auth import AuthContext


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
        id=1,
        organization_id="org-current",
        name="Test",
        provider_type="openai",
        api_key="test-key",
        is_active=True,
    )
    mock_session.items.append(p)

    resp = auth_client.post(
        "/api/prompts/test",
        json={
            "content": "Summarize this: {{email}}",
            "variables": {"email": "hello world"},
        },
        headers={"X-User-Id": "testuser", "X-Organization-Id": "org-current"},
    )

    assert resp.status_code == 200
    assert resp.json()["result"] == "Mocked LLM result"


class QueryAwarePromptSession:
    def __init__(self):
        self.other_org_provider = LLMProvider(
            id=1,
            organization_id="org-other",
            name="Other Org",
            provider_type="openai",
            api_key="other-org-key",
            is_active=True,
        )
        self.user_tenant_config = TenantConfig(
            user_id="testuser", openai_api_key="legacy-user-key"
        )

    async def execute(self, stmt):
        statement = str(stmt).lower()
        if "llm_providers" in statement:
            if "llm_providers.organization_id" in statement:
                return _ListResult([])
            return _ListResult([self.other_org_provider])
        if "tenant_configs" in statement:
            return _ListResult([self.user_tenant_config])
        return _ListResult([])


class _ListResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items


def test_prompt_test_fails_closed_without_active_provider_for_current_org(monkeypatch):
    import api.prompts as prompts_module

    called = False

    async def mock_execute(*args, **kwargs):
        nonlocal called
        called = True
        return {"result": "should not execute"}

    monkeypatch.setattr(prompts_module, "execute_prompt_with_llm", mock_execute)
    app.dependency_overrides[get_db] = lambda: QueryAwarePromptSession()

    with TestClient(
        app, headers={"X-User-Id": "testuser", "X-Organization-Id": "org-current"}
    ) as c:
        resp = c.post(
            "/api/prompts/test",
            json={
                "content": "Summarize this: {{email}}",
                "variables": {"email": "hello world"},
            },
        )

    assert resp.status_code == 400
    assert resp.json() == {"detail": "LLM API key not configured"}
    assert called is False


def test_prompt_list_statement_scopes_shared_prompts_to_current_org():
    from api.prompts import build_prompt_list_statement

    auth_context = AuthContext(
        user_id="testuser",
        role="member",
        organization_id="org-current",
        group_ids=(),
        workspace_id="workspace-org-current",
    )

    statement = build_prompt_list_statement(auth_context)
    sql = str(statement).lower()
    params = statement.compile().params

    assert "prompt_templates.organization_id" in sql
    assert "prompt_templates.is_shared" in sql
    assert "created_by" in sql
    assert "org-current" in params.values()


def test_prompt_create_rejects_shared_prompt_without_org_scope(auth_client):
    response = auth_client.post(
        "/api/prompts",
        json={
            "title": "Shared Prompt",
            "content": "Summarize this: {{email}}",
            "is_shared": True,
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Shared prompts require organization scope"}
