import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from db.models import Email
from main import app
import datetime
from unittest.mock import patch


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class MockTenantConfig:
    def __init__(self):
        self.smtp_server = "93.184.216.34"
        self.smtp_port = 587
        self.smtp_username = "testuser"


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


class OwnerAwareMockSession(LimitAwareMockSession):
    def __init__(self, items, current_user: str, tenant_config=_DEFAULT_TENANT_CONFIG):
        super().__init__(items, tenant_config=tenant_config)
        self.current_user = current_user
        self.executed_sql: list[str] = []

    async def execute(self, query):
        self.executed_sql.append(str(query).lower())
        original_items = self.items
        if "emails.user_id" in self.executed_sql[-1]:
            self.items = [
                item
                for item in self.items
                if getattr(item, "user_id", None) == self.current_user
            ]
        try:
            return await super().execute(query)
        finally:
            self.items = original_items


@pytest.fixture
def sample_email():
    return Email(
        id=1,
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
async def test_get_email_by_id(client: AsyncClient, db_session, sample_email: Email):
    response = await client.get(f"/api/emails/{sample_email.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_email.id
    assert response.json()["reply_to"] == "reply@example.com"


@pytest.mark.asyncio
async def test_get_email_by_id_returns_server_sanitized_body(
    client: AsyncClient, db_session, sample_email: Email
):
    sample_email.body = (
        "Hello <img src=x onerror=\"alert('xss')\">"
        "<script>alert(document.cookie)</script>"
    )

    response = await client.get(f"/api/emails/{sample_email.id}")

    assert response.status_code == 200
    body = response.json()["body"]
    assert "Hello" in body
    assert "<script" not in body.lower()
    assert "onerror" not in body.lower()
    assert "document.cookie" not in body


@pytest.mark.asyncio
async def test_get_emails_uses_server_sanitized_snippet(
    client: AsyncClient, db_session, sample_email: Email
):
    sample_email.body = "Preview <svg onload=alert(1)>payload</svg>"

    response = await client.get("/api/emails?limit=10")

    assert response.status_code == 200
    snippet = response.json()["emails"][0]["snippet"]
    assert "Preview" in snippet
    assert "<svg" not in snippet.lower()
    assert "onload" not in snippet.lower()


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


def owned_email(email_id: int, owner: str, thread_id: str = "shared-thread") -> Email:
    email = Email(
        id=email_id,
        message_id=f"msg-{email_id}@example.com",
        thread_id=thread_id,
        sender=f"sender-{email_id}@example.com",
        recipients=f"{owner}@example.com",
        subject=f"Owner {owner}",
        date=datetime.datetime(2026, 4, 27, 10, email_id, tzinfo=datetime.timezone.utc),
        body=f"Body for {owner}",
    )
    email.user_id = owner
    return email


def override_email_user(user_id: str):
    async def _override():
        return user_id

    return _override


@pytest.mark.asyncio
async def test_get_email_by_id_returns_404_for_other_user(client: AsyncClient):
    from db.session import get_db
    from api.emails import get_current_user as emails_get_current_user

    session = OwnerAwareMockSession([owned_email(7, "bob")], current_user="alice")
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[emails_get_current_user] = override_email_user("alice")

    response = await client.get("/api/emails/7")

    assert response.status_code == 404
    assert any("emails.user_id" in sql for sql in session.executed_sql)


@pytest.mark.asyncio
async def test_get_emails_lists_only_current_user_threads(client: AsyncClient):
    from db.session import get_db
    from api.emails import get_current_user as emails_get_current_user

    alice_email = owned_email(1, "alice", thread_id="alice-thread")
    bob_email = owned_email(2, "bob", thread_id="bob-thread")
    session = OwnerAwareMockSession([bob_email, alice_email], current_user="alice")
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[emails_get_current_user] = override_email_user("alice")

    response = await client.get("/api/emails?limit=10")

    assert response.status_code == 200
    data = response.json()["emails"]
    assert [item["id"] for item in data] == [alice_email.id]
    assert any("emails.user_id" in sql for sql in session.executed_sql)


@pytest.mark.asyncio
async def test_get_email_thread_excludes_other_user_messages(client: AsyncClient):
    from db.session import get_db
    from api.emails import get_current_user as emails_get_current_user

    alice_email = owned_email(1, "alice")
    bob_email = owned_email(2, "bob")
    session = OwnerAwareMockSession([alice_email, bob_email], current_user="alice")
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[emails_get_current_user] = override_email_user("alice")

    response = await client.get("/api/emails/thread/shared-thread")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["thread"]] == [alice_email.id]
    assert any("emails.user_id" in sql for sql in session.executed_sql)


@pytest.mark.asyncio
async def test_get_email_thread_returns_404_when_thread_belongs_only_to_other_user(
    client: AsyncClient,
):
    from db.session import get_db
    from api.emails import get_current_user as emails_get_current_user

    session = OwnerAwareMockSession([owned_email(2, "bob")], current_user="alice")
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[emails_get_current_user] = override_email_user("alice")

    response = await client.get("/api/emails/thread/shared-thread")

    assert response.status_code == 404
    assert any("emails.user_id" in sql for sql in session.executed_sql)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    ["/api/emails?limit=10", "/api/emails/1", "/api/emails/thread/thread123"],
)
async def test_get_email_routes_apply_auth_dependency(client: AsyncClient, path: str):
    from api.emails import get_current_user as emails_get_current_user

    calls = []

    async def auth_override():
        calls.append("hit")
        return "authorized-user"

    app.dependency_overrides[emails_get_current_user] = auth_override

    response = await client.get(path)

    assert response.status_code == 200
    assert calls == ["hit"]


@patch("api.emails.send_email", return_value={"status": "simulated", "simulated": True})
def test_send_email_endpoint(mock_send_email):
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

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
    mock_send_email.assert_called_once_with(
        "test@example.com",
        "Re: Test",
        "This is a reply.",
        smtp_server="93.184.216.34",
        smtp_port=587,
        smtp_username="testuser",
        in_reply_to="<parent@example.com>",
        references="<root@example.com> <parent@example.com>",
    )


def test_send_email_endpoint_preserves_configuration_error(sample_email):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    async def missing_smtp_db():
        yield MockSession([sample_email], tenant_config=None)

    app.dependency_overrides[get_db] = missing_smtp_db
    try:
        client = TestClient(app)
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


def test_send_email_endpoint_rejects_unsafe_legacy_smtp_config(sample_email):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    class UnsafeTenantConfig:
        smtp_server = "127.0.0.1"
        smtp_port = 587
        smtp_username = "testuser"

    async def unsafe_smtp_db():
        yield MockSession([sample_email], tenant_config=UnsafeTenantConfig())

    app.dependency_overrides[get_db] = unsafe_smtp_db
    try:
        client = TestClient(app)
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
    assert "not allowed" in response.json()["detail"]


@patch("api.emails.send_email", return_value={"status": "simulated", "simulated": True})
def test_send_email_endpoint_validates_unsafe_smtp_before_send(
    mock_send_email, sample_email
):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    class UnsafeTenantConfig:
        smtp_server = "169.254.169.254"
        smtp_port = 587
        smtp_username = "testuser"

    async def unsafe_smtp_db():
        yield MockSession([sample_email], tenant_config=UnsafeTenantConfig())

    app.dependency_overrides[get_db] = unsafe_smtp_db
    try:
        client = TestClient(app)
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
    assert "not allowed" in response.json()["detail"]
    mock_send_email.assert_not_called()


@patch("api.emails.send_email", return_value={"status": "simulated", "simulated": True})
def test_send_email_endpoint_uses_resolver_pinned_smtp_address(
    mock_send_email,
    sample_email,
    monkeypatch,
):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    class HostnameTenantConfig:
        smtp_server = "smtp.example.com"
        smtp_port = 587
        smtp_username = "testuser"

    monkeypatch.setattr(
        "services.mail_endpoint_policy.socket.getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 587))],
    )

    async def hostname_smtp_db():
        yield MockSession([sample_email], tenant_config=HostnameTenantConfig())

    app.dependency_overrides[get_db] = hostname_smtp_db
    try:
        client = TestClient(app)
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

    assert response.status_code == 200
    mock_send_email.assert_called_once_with(
        "test@example.com",
        "Re: Test",
        "This is a reply.",
        smtp_server="93.184.216.34",
        smtp_port=587,
        smtp_username="testuser",
        in_reply_to=None,
        references=None,
    )


@patch("api.emails.send_email", return_value={"status": "failed", "simulated": False})
def test_send_email_endpoint_rejects_failed_send_status(mock_send_email):
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

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
