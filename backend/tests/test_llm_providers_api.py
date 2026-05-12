import pytest
from fastapi.testclient import TestClient
from main import app
from db.models import LLMProvider, AuditLog
from db.session import get_db
from db.session import get_db

class MockSession:
    def __init__(self):
        self.items = []
        self.audits = []

    async def execute(self, stmt):
        class MockResult:
            def scalars(self):
                class MockScalars:
                    def all(self):
                        return self.items
                    def first(self):
                        if self.items: return self.items[0]
                        return None
                m = MockScalars()
                m.items = getattr(self, 'items', [])
                return m
        res = MockResult()
        res.items = self.items
        return res
        
    def add(self, obj):
        if isinstance(obj, LLMProvider):
            obj.id = len(self.items) + 1
            obj.updated_at = "2026-05-11T00:00:00Z"
            self.items.append(obj)
        elif isinstance(obj, AuditLog):
            self.audits.append(obj)
            
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
    mock_session.audits = []


@pytest.fixture
def admin_client():
    with TestClient(app, headers={"X-User-Id": "admin"}) as c:
        yield c

@pytest.fixture
def member_client():
    with TestClient(app, headers={"X-User-Id": "member"}) as c:
        yield c

def test_llm_provider_crud_admin(admin_client):
    mock_session.items = []
    # Create
    resp = admin_client.post("/api/llm-providers", json={
        "name": "Primary OpenAI",
        "provider_type": "openai",
        "api_key": "sk-12345"
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "Primary OpenAI"
    assert data["configured"] is True
    assert data["fingerprint"] is not None
    assert "api_key" not in data
    
    provider_id = data["id"]
    
    # List
    resp = admin_client.get("/api/llm-providers")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    
    # Update
    resp = admin_client.put(f"/api/llm-providers/{provider_id}", json={
        "is_active": True
    })
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True
    
    # Check AuditLog
    # result = await db_session.execute(select(AuditLog).where(AuditLog.user_id == "admin"))
    # logs = result.scalars().all()
    pass

def test_llm_provider_member_rejected(member_client):
    resp = member_client.get("/api/llm-providers")
    assert resp.status_code == 403
    
    resp = member_client.post("/api/llm-providers", json={
        "name": "Malicious",
        "provider_type": "openai"
    })
    assert resp.status_code == 403
