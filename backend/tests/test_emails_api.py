import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from db.models import Email
from main import app
import datetime
from unittest.mock import patch

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        headers={"X-User-Id": "testuser"},
        base_url="http://test",
    ) as ac:
        yield ac


class MockTenantConfig:
    def __init__(self):
        self.smtp_server = "smtp.example.com"
        self.smtp_port = 587
        self.smtp_username = "testuser"
        self.smtp_password = None


_DEFAULT_TENANT_CONFIG = object()


class MockSession:
    def __init__(self, items, tenant_config=_DEFAULT_TENANT_CONFIG):
        self.items = items
        self.tenant_config = (
            MockTenantConfig()
            if tenant_config is _DEFAULT_TENANT_CONFIG
            else tenant_config
        )

    async def execute(self, query):
        class MockResult:
            def __init__(self, rows):
                self.rows = rows

            def scalars(self):
                return self

            def all(self):
                return self.rows

            def scalar_one_or_none(self):
                return self.rows[0] if self.rows else None

        if "tenant_configs" in compiled_query_text(query):
            rows = [] if self.tenant_config is None else [self.tenant_config]
            return MockResult(rows)
        return MockResult(self.items)

    async def scalar(self, query):
        return self.tenant_config


class LimitAwareMockSession(MockSession):
    def __init__(self, items, tenant_config=_DEFAULT_TENANT_CONFIG):
        super().__init__(items, tenant_config=tenant_config)
        self.last_limit_value = None

    async def execute(self, query):
        class MockResult:
            def __init__(self, rows):
                self.rows = rows

            def scalars(self):
                return self

            def all(self):
                return self.rows

            def scalar_one_or_none(self):
                return self.rows[0] if self.rows else None

        limit_clause = getattr(query, "_limit_clause", None)
        limit_value = getattr(limit_clause, "value", None)
        self.last_limit_value = limit_value
        rows = self.items[:limit_value] if limit_value else self.items
        return MockResult(rows)


class QueryCapturingSession(MockSession):
    def __init__(self, items, tenant_config=_DEFAULT_TENANT_CONFIG):
        super().__init__(items, tenant_config=tenant_config)
        self.queries = []

    async def execute(self, query):
        self.queries.append(query)
        return await super().execute(query)


class ScalarQueryCapturingSession(MockSession):
    def __init__(self, items, tenant_config=_DEFAULT_TENANT_CONFIG):
        super().__init__(items, tenant_config=tenant_config)
        self.scalar_queries = []

    async def scalar(self, query):
        self.scalar_queries.append(query)
        return await super().scalar(query)


def compiled_query_text(query) -> str:
    return str(query).lower()


def compiled_query_params(query) -> dict[str, object]:
    return dict(query.compile().params)


def assert_query_is_owner_scoped(query) -> None:
    query_text = compiled_query_text(query)
    query_params = compiled_query_params(query)

    assert "emails.user_id = :user_id_1" in query_text
    assert "emails.organization_id = :organization_id_1" in query_text
    assert query_params["user_id_1"] == "testuser"
    assert query_params["organization_id_1"] == "org-acme"


@pytest.fixture
def sample_email():
    return Email(
        id=1,
        user_id="testuser",
        message_id="msg123",
        thread_id="thread123",
        sender="test@example.com",
        reply_to="reply@example.com",
        recipients="user@example.com",
        subject="Test Subject",
        date=datetime.datetime.now(datetime.timezone.utc),
        body="This is a test email body.",
    )


@pytest.fixture
def db_session(sample_email):
    # Mock the database session
    return MockSession([sample_email])


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    from db.session import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_emails(client: AsyncClient, db_session):
    response = await client.get("/api/emails?limit=10")
    assert response.status_code == 200
    assert "emails" in response.json()


@pytest.mark.asyncio
async def test_get_emails_returns_exact_distinct_threads_beyond_overfetch_window(
    client: AsyncClient, db_session
):
    hot_thread = [
        Email(
            id=index + 1,
            user_id="testuser",
            message_id=f"hot-{index}",
            thread_id="hot-thread",
            sender="hot@example.com",
            recipients="user@example.com",
            subject="Hot thread",
            date=datetime.datetime(
                2026, 4, 27, 12, index, tzinfo=datetime.timezone.utc
            ),
            body=f"Hot body {index}",
        )
        for index in range(6)
    ]
    second_thread = Email(
        id=99,
        user_id="testuser",
        message_id="second-thread-root",
        thread_id="second-thread",
        sender="second@example.com",
        recipients="user@example.com",
        subject="Second thread",
        date=datetime.datetime(2026, 4, 27, 10, 0, tzinfo=datetime.timezone.utc),
        body="Second body",
    )
    db_session.items = sorted(
        [*hot_thread, second_thread], key=lambda item: item.date, reverse=True
    )

    from db.session import get_db

    app.dependency_overrides[get_db] = lambda: LimitAwareMockSession(db_session.items)

    response = await client.get("/api/emails?limit=2")

    assert response.status_code == 200
    data = response.json()["emails"]
    assert [item["thread_id"] for item in data] == ["hot-thread", "second-thread"]
    assert data[0]["reply_count"] == 6


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [0, -1])
async def test_get_emails_rejects_non_positive_limit(client: AsyncClient, limit: int):
    response = await client.get(f"/api/emails?limit={limit}")

    assert response.status_code == 422
    assert "limit" in response.text


@pytest.mark.asyncio
async def test_get_emails_bounds_database_candidate_window(
    client: AsyncClient, db_session
):
    from db.session import get_db

    session = LimitAwareMockSession(db_session.items)
    app.dependency_overrides[get_db] = lambda: session

    response = await client.get("/api/emails?limit=10")

    assert response.status_code == 200
    assert session.last_limit_value is not None
    assert session.last_limit_value >= 10


@pytest.mark.asyncio
async def test_get_emails_normalizes_legacy_bracketed_thread_ids(
    client: AsyncClient, db_session
):
    root = Email(
        id=1,
        user_id="testuser",
        message_id="<root@example.com>",
        thread_id="<root@example.com>",
        sender="root@example.com",
        recipients="user@example.com",
        subject="Legacy root",
        date=datetime.datetime(2026, 4, 27, 10, 0, tzinfo=datetime.timezone.utc),
        body="Root body",
    )
    reply = Email(
        id=2,
        user_id="testuser",
        message_id="<reply@example.com>",
        thread_id="root@example.com",
        sender="reply@example.com",
        recipients="user@example.com",
        subject="Re: Legacy root",
        date=datetime.datetime(2026, 4, 27, 11, 0, tzinfo=datetime.timezone.utc),
        body="Reply body",
    )
    db_session.items = [reply, root]

    response = await client.get("/api/emails?limit=10")

    assert response.status_code == 200
    data = response.json()["emails"]
    assert len(data) == 1
    assert data[0]["thread_id"] == "root@example.com"
    assert data[0]["reply_count"] == 2


@pytest.mark.asyncio
async def test_get_emails_marks_self_sent_and_pending_reply_threads(
    client: AsyncClient, db_session
):
    class MailTenantConfig:
        smtp_username = "Me <testuser@example.com>"
        imap_username = None

    sent_waiting = Email(
        id=10,
        user_id="testuser",
        message_id="waiting-msg",
        thread_id="waiting-thread",
        sender="Test User <testuser@example.com>",
        recipients="target@example.com",
        subject="Can you confirm?",
        date=datetime.datetime(2026, 4, 27, 10, 0, tzinfo=datetime.timezone.utc),
        body="Please reply when you can.",
    )
    self_note = Email(
        id=11,
        user_id="testuser",
        message_id="note-msg",
        thread_id="note-thread",
        sender="testuser@example.com",
        recipients="testuser@example.com",
        subject="Note to self",
        date=datetime.datetime(2026, 4, 27, 11, 0, tzinfo=datetime.timezone.utc),
        body="Summarize this as knowledge.",
    )
    db_session.tenant_config = MailTenantConfig()
    db_session.items = [self_note, sent_waiting]

    response = await client.get("/api/emails?limit=10")

    assert response.status_code == 200
    by_thread = {item["thread_id"]: item for item in response.json()["emails"]}
    assert by_thread["waiting-thread"]["requires_reply"] is True
    assert by_thread["waiting-thread"]["is_self_sent"] is False
    assert by_thread["note-thread"]["is_self_sent"] is True
    assert by_thread["note-thread"]["requires_reply"] is False


@pytest.mark.asyncio
async def test_get_email_by_id(client: AsyncClient, db_session, sample_email: Email):
    response = await client.get(f"/api/emails/{sample_email.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_email.id
    assert response.json()["reply_to"] == "reply@example.com"


@pytest.mark.asyncio
async def test_get_email_thread(client: AsyncClient, db_session, sample_email: Email):
    response = await client.get(f"/api/emails/thread/{sample_email.thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert "thread" in data
    assert len(data["thread"]) == 1
    assert data["thread"][0]["id"] == sample_email.id


@pytest.mark.asyncio
async def test_get_email_thread_returns_chronological_order(
    client: AsyncClient, db_session
):
    newer = Email(
        id=2,
        user_id="testuser",
        message_id="newer-msg",
        thread_id="thread123",
        sender="newer@example.com",
        recipients="user@example.com",
        subject="Re: Test Subject",
        date=datetime.datetime(2026, 4, 27, 11, 0, tzinfo=datetime.timezone.utc),
        body="Newer body",
    )
    older = Email(
        id=1,
        user_id="testuser",
        message_id="older-msg",
        thread_id="thread123",
        sender="older@example.com",
        recipients="user@example.com",
        subject="Test Subject",
        date=datetime.datetime(2026, 4, 27, 10, 0, tzinfo=datetime.timezone.utc),
        body="Older body",
    )
    db_session.items = [newer, older]

    response = await client.get("/api/emails/thread/thread123")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["thread"]] == [1, 2]


@pytest.mark.asyncio
async def test_get_email_thread_accepts_url_encoded_reserved_characters(
    client: AsyncClient, db_session, sample_email: Email
):
    sample_email.thread_id = "root/part@example.com"
    sample_email.message_id = "<root/part@example.com>"

    response = await client.get("/api/emails/thread/root%2Fpart%40example.com")

    assert response.status_code == 200
    assert response.json()["thread"][0]["thread_id"] == "root/part@example.com"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    ["/api/emails?limit=10", "/api/emails/1", "/api/emails/thread/thread123"],
)
async def test_get_email_routes_apply_auth_dependency(client: AsyncClient, path: str):
    from api.auth import AuthContext
    from api.emails import get_auth_context as emails_get_auth_context

    calls = []

    async def auth_override():
        calls.append("hit")
        return AuthContext(
            user_id="authorized-user",
            role="member",
            organization_id="authorized-org",
            group_ids=(),
            workspace_id="workspace-authorized-org",
        )

    app.dependency_overrides[emails_get_auth_context] = auth_override

    response = await client.get(path)

    assert response.status_code == 200
    assert calls == ["hit"]


@pytest.mark.asyncio
async def test_get_emails_query_is_scoped_to_current_user(
    client: AsyncClient, sample_email: Email
):
    from db.session import get_db

    session = QueryCapturingSession([sample_email])
    app.dependency_overrides[get_db] = lambda: session

    response = await client.get(
        "/api/emails?limit=10",
        headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
    )

    assert response.status_code == 200
    assert_query_is_owner_scoped(session.queries[-1])


@pytest.mark.asyncio
async def test_get_email_by_id_query_is_scoped_to_current_user(
    client: AsyncClient, sample_email: Email
):
    from db.session import get_db

    session = QueryCapturingSession([sample_email])
    app.dependency_overrides[get_db] = lambda: session

    response = await client.get(
        f"/api/emails/{sample_email.id}",
        headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
    )

    assert response.status_code == 200
    assert_query_is_owner_scoped(session.queries[-1])


@pytest.mark.asyncio
async def test_get_email_thread_query_is_scoped_to_current_user(
    client: AsyncClient, sample_email: Email
):
    from db.session import get_db

    session = QueryCapturingSession([sample_email])
    app.dependency_overrides[get_db] = lambda: session

    response = await client.get(
        f"/api/emails/thread/{sample_email.thread_id}",
        headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
    )

    assert response.status_code == 200
    assert_query_is_owner_scoped(session.queries[-1])


@patch("api.emails.send_email", return_value={"status": "simulated", "simulated": True})
def test_send_email_endpoint(mock_send_email, monkeypatch):
    from main import app
    from fastapi.testclient import TestClient

    validate_calls = []

    def fake_validate_smtp_destination(smtp_server, smtp_port, *, resolve_host=True):
        validate_calls.append(resolve_host)
        return smtp_server, smtp_port

    monkeypatch.setattr(
        "api.emails.validate_smtp_destination", fake_validate_smtp_destination
    )

    client = TestClient(app, headers={"X-User-Id": "testuser"})

    response = client.post(
        "/api/emails/send",
        json={
            "to": "test@example.com",
            "subject": "Re: Test",
            "body": "This is a reply.",
            "in_reply_to": "<parent@example.com>",
            "references": "<root@example.com> <parent@example.com>",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "simulated", "simulated": True}
    assert validate_calls == [True]
    mock_send_email.assert_called_once_with(
        "test@example.com",
        "Re: Test",
        "This is a reply.",
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_username="testuser",
        smtp_password=None,
        in_reply_to="<parent@example.com>",
        references="<root@example.com> <parent@example.com>",
    )


@patch("api.emails.send_email", return_value={"status": "simulated", "simulated": True})
def test_send_email_endpoint_ignores_user_id_query_and_uses_authenticated_user_config(
    mock_send_email, monkeypatch, sample_email
):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    def fake_validate_smtp_destination(smtp_server, smtp_port, *, resolve_host=True):
        return smtp_server, smtp_port

    monkeypatch.setattr(
        "api.emails.validate_smtp_destination", fake_validate_smtp_destination
    )
    session = ScalarQueryCapturingSession([sample_email])

    async def tenant_db():
        yield session

    app.dependency_overrides[get_db] = tenant_db
    try:
        client = TestClient(app, headers={"X-User-Id": "testuser"})
        response = client.post(
            "/api/emails/send?user_id=victim-user",
            json={
                "to": "test@example.com",
                "subject": "Re: Test",
                "body": "This is a reply.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert compiled_query_params(session.scalar_queries[-1])["user_id_1"] == "testuser"
    mock_send_email.assert_called_once()


def test_send_email_endpoint_preserves_configuration_error(sample_email):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    async def missing_smtp_db():
        yield MockSession([sample_email], tenant_config=None)

    app.dependency_overrides[get_db] = missing_smtp_db
    try:
        client = TestClient(app, headers={"X-User-Id": "testuser"})
        response = client.post(
            "/api/emails/send",
            json={
                "to": "test@example.com",
                "subject": "Re: Test",
                "body": "This is a reply.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "SMTP is not configured"}


@patch("api.emails.send_email", return_value={"status": "sent", "simulated": False})
def test_send_email_endpoint_rejects_unsafe_persisted_smtp_host(mock_send_email):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    class UnsafeTenantConfig(MockTenantConfig):
        def __init__(self):
            super().__init__()
            self.smtp_server = "127.0.0.1"
            self.smtp_port = 587

    async def unsafe_smtp_db():
        yield MockSession([], tenant_config=UnsafeTenantConfig())

    app.dependency_overrides[get_db] = unsafe_smtp_db
    try:
        client = TestClient(app, headers={"X-User-Id": "testuser"})
        response = client.post(
            "/api/emails/send",
            json={
                "to": "test@example.com",
                "subject": "Test",
                "body": "Body",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "SMTP server is not allowed" in response.json()["detail"]
    mock_send_email.assert_not_called()


@patch("api.emails.send_email", return_value={"status": "failed", "simulated": False})
def test_send_email_endpoint_rejects_failed_send_status(mock_send_email, monkeypatch):
    from main import app
    from fastapi.testclient import TestClient

    def fake_validate_smtp_destination(smtp_server, smtp_port, *, resolve_host=True):
        assert resolve_host is True
        return smtp_server, smtp_port

    monkeypatch.setattr(
        "api.emails.validate_smtp_destination", fake_validate_smtp_destination
    )

    client = TestClient(app, headers={"X-User-Id": "testuser"})

    response = client.post(
        "/api/emails/send",
        json={
            "to": "test@example.com",
            "subject": "Re: Test",
            "body": "This is a reply.",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to send email"}
    mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_get_pending_replies(client: AsyncClient, db_session):
    from main import app
    from db.session import get_db

    # Create MockTenantConfig with smtp_username set to match one email
    class SentTenantConfig:
        smtp_username = "testuser@example.com"
        imap_username = None
        
    db_session.tenant_config = SentTenantConfig()

    sent_email = Email(
        id=3,
        user_id="testuser",
        message_id="msg3",
        thread_id="thread3",
        sender="testuser@example.com",
        recipients="target@example.com",
        subject="Did you get this?",
        date=datetime.datetime(2026, 4, 28, 10, 0, tzinfo=datetime.timezone.utc),
        body="Please reply when you can.",
    )
    answered_sent_email = Email(
        id=4,
        user_id="testuser",
        message_id="msg4",
        thread_id="thread4",
        sender="testuser@example.com",
        recipients="target@example.com",
        subject="Answered thread",
        date=datetime.datetime(2026, 4, 28, 9, 0, tzinfo=datetime.timezone.utc),
        body="Please reply when you can.",
    )
    external_reply = Email(
        id=5,
        user_id="testuser",
        message_id="msg5",
        thread_id="thread4",
        sender="target@example.com",
        recipients="testuser@example.com",
        subject="Re: Answered thread",
        date=datetime.datetime(2026, 4, 28, 11, 0, tzinfo=datetime.timezone.utc),
        body="Confirmed.",
    )
    
    db_session.items = [sent_email, answered_sent_email, external_reply]

    app.dependency_overrides[get_db] = lambda: db_session

    response = await client.get("/api/emails/pending-replies")
    assert response.status_code == 200
    data = response.json()
    assert len(data["emails"]) == 1
    assert data["emails"][0]["sender"] == "testuser@example.com"
    assert data["emails"][0]["thread_id"] == "thread3"
    assert data["emails"][0]["requires_reply"] is True
