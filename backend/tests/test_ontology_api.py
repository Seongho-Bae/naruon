import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")

class MockRow:
    def __init__(
        self,
        sender_email,
        relationship_type,
        confidence_score,
        parent_sender_email=None,
        source_message_id=None,
        source_thread_id=None,
    ):
        self.sender_email = sender_email
        self.relationship_type = relationship_type
        self.confidence_score = confidence_score
        self.parent_sender_email = parent_sender_email
        self.source_message_id = source_message_id
        self.source_thread_id = source_thread_id

class MockResult:
    def __init__(self, items):
        self.items = items
        
    def scalars(self):
        return self
        
    def all(self):
        return self.items
        
    def first(self):
        return self.items[0] if self.items else None

class MockSession:
    def __init__(self):
        self.items = [
            MockRow(
                "boss@example.com",
                "manager",
                0.95,
                "ceo@example.com",
                "<q2@example.com>",
                "thread-q2",
            )
        ]
        self.statements = []
        
    async def execute(self, stmt):
        self.statements.append(stmt)
        compiled = str(stmt)
        # SQLAlchemy select compiled string won't contain vendor@example.com literally.
        # But we can check if it's the GET request by looking at the statement.
        # A safer mock for the test is to just return empty list if we detect a specific query.
        if "sender_email =" in compiled:
            return MockResult([])
        return MockResult(self.items)

    def add(self, obj):
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

class ExistingRelationshipSession(MockSession):
    def __init__(self):
        super().__init__()
        self.items = [MockRow("vendor@example.com", "vendor", 0.5, "buyer@example.com")]

    async def execute(self, stmt):
        return MockResult(self.items)

async def override_get_db():
    yield MockSession()

@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_relationships(client: TestClient):
    resp = client.get(
        "/api/ontology/relationships",
        params={"source_message_id": "<q2@example.com>", "source_thread_id": "thread-q2"},
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["sender_email"] == "boss@example.com"
    assert items[0]["parent_sender_email"] == "ceo@example.com"
    assert items[0]["source_message_id"] == "<q2@example.com>"
    assert items[0]["source_thread_id"] == "thread-q2"
    assert items[0]["relationship_type"] == "manager"
    assert items[0]["next_action"] == "classify_sender"


def test_get_relationships_filters_by_source_and_owner_scope():
    session = MockSession()

    async def override_scoped_get_db():
        yield session

    app.dependency_overrides[get_db] = override_scoped_get_db
    try:
        with TestClient(app, headers={"X-User-Id": "testuser"}) as test_client:
            resp = test_client.get(
                "/api/ontology/relationships",
                params={
                    "source_message_id": "<q2@example.com>",
                    "source_thread_id": "thread-q2",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    query_text = str(session.statements[-1]).lower()
    assert "sender_relationships.user_id" in query_text
    assert "sender_relationships.organization_id" in query_text
    assert "sender_relationships.source_message_id" in query_text
    assert "sender_relationships.source_thread_id" in query_text

def test_create_relationship(client: TestClient):
    resp = client.post(
        "/api/ontology/relationships",
        json={
            "sender_email": "vendor@example.com",
            "parent_sender_email": "buyer@example.com",
            "source_message_id": "<vendor@example.com>",
            "source_thread_id": "thread-vendor",
            "relationship_type": "vendor",
            "confidence_score": 0.8
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sender_email"] == "vendor@example.com"
    assert data["parent_sender_email"] == "buyer@example.com"
    assert data["source_message_id"] == "<vendor@example.com>"
    assert data["source_thread_id"] == "thread-vendor"
    assert data["relationship_type"] == "vendor"
    assert data["next_action"] == "prepare_response_draft"


def test_update_relationship_preserves_existing_parent_when_omitted():
    async def override_existing_get_db():
        yield ExistingRelationshipSession()

    app.dependency_overrides[get_db] = override_existing_get_db
    try:
        with TestClient(app, headers={"X-User-Id": "testuser"}) as test_client:
            resp = test_client.post(
                "/api/ontology/relationships",
                json={
                    "sender_email": "vendor@example.com",
                    "relationship_type": "customer",
                    "confidence_score": 0.7,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["sender_email"] == "vendor@example.com"
    assert data["parent_sender_email"] == "buyer@example.com"
    assert data["relationship_type"] == "customer"
