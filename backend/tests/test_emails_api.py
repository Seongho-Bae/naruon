import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from db.models import Email
from main import app
import datetime
from unittest.mock import patch
from tests.auth_helpers import auth_headers


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        headers=auth_headers("testuser"),
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
    def __init__(
        self,
        items,
        tenant_config=_DEFAULT_TENANT_CONFIG,
        mailbox_account_ids=None,
    ):
        self.items = items
        self.tenant_config = (
            MockTenantConfig()
            if tenant_config is _DEFAULT_TENANT_CONFIG
            else tenant_config
        )
        self.mailbox_account_ids = set(mailbox_account_ids or {1, 2, 3})

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

        params = query.compile().params
        rows = list(self.items)
        user_id = next(
            (value for key, value in params.items() if "user_id" in key), None
        )
        mailbox_account_id = next(
            (value for key, value in params.items() if "mailbox_account_id" in key),
            None,
        )
        item_id = next(
            (value for key, value in params.items() if key.startswith("id_")), None
        )
        if user_id is not None:
            rows = [row for row in rows if getattr(row, "user_id", None) == user_id]
        if mailbox_account_id is not None:
            rows = [
                row
                for row in rows
                if getattr(row, "mailbox_account_id", None)
                in {None, mailbox_account_id}
            ]
        if item_id is not None:
            rows = [row for row in rows if row.id == item_id]
        return MockResult(rows)

    async def scalar(self, query):
        query_text = str(query).lower()
        if "from mailbox_accounts" in query_text:
            params = query.compile().params
            mailbox_account_id = next(
                (value for key, value in params.items() if "id" in key),
                None,
            )
            return (
                mailbox_account_id
                if mailbox_account_id in self.mailbox_account_ids
                else None
            )
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

        params = query.compile().params
        user_id = next(
            (value for key, value in params.items() if "user_id" in key), None
        )
        mailbox_account_id = next(
            (value for key, value in params.items() if "mailbox_account_id" in key),
            None,
        )
        rows = list(self.items)
        if user_id is not None:
            rows = [row for row in rows if getattr(row, "user_id", None) == user_id]
        if mailbox_account_id is not None:
            rows = [
                row
                for row in rows
                if getattr(row, "mailbox_account_id", None)
                in {None, mailbox_account_id}
            ]
        limit_clause = getattr(query, "_limit_clause", None)
        limit_value = getattr(limit_clause, "value", None)
        self.last_limit_value = limit_value
        rows = rows[:limit_value] if limit_value else rows
        return MockResult(rows)


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
    db_session.items[0].mailbox_account_id = 1
    response = await client.get("/api/emails?limit=10")
    assert response.status_code == 200
    assert "emails" in response.json()
    assert response.json()["emails"][0]["mailbox_account_id"] == 1


@pytest.mark.asyncio
async def test_get_emails_sanitizes_legacy_html_snippet(
    client: AsyncClient, db_session, sample_email: Email
):
    sample_email.body = '<p>Safe list text</p><img src="x" onerror="alert(1)">'

    response = await client.get("/api/emails?limit=10")

    assert response.status_code == 200
    snippet = response.json()["emails"][0]["snippet"]
    assert "Safe list text" in snippet
    assert "<img" not in snippet
    assert "onerror" not in snippet
    assert "alert(" not in snippet


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
async def test_get_email_by_id(client: AsyncClient, db_session, sample_email: Email):
    sample_email.mailbox_account_id = 3
    response = await client.get(f"/api/emails/{sample_email.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_email.id
    assert response.json()["reply_to"] == "reply@example.com"
    assert response.json()["mailbox_account_id"] == 3


@pytest.mark.asyncio
async def test_get_email_by_id_escapes_legacy_html_body(
    client: AsyncClient, db_session, sample_email: Email
):
    sample_email.body = (
        '<p>Safe text</p><img src="x" onerror="alert(1)"><script>alert(2)</script>'
    )

    response = await client.get(f"/api/emails/{sample_email.id}")

    assert response.status_code == 200
    body = response.json()["body"]
    assert "Safe text" in body
    assert "<img" not in body
    assert "<script" not in body
    assert "onerror=" not in body
    assert "alert(" not in body


@pytest.mark.asyncio
async def test_get_email_by_id_sanitizes_entity_encoded_html_body(
    client: AsyncClient, db_session, sample_email: Email
):
    sample_email.body = (
        "&lt;p&gt;Safe text&lt;/p&gt;&lt;img src=x "
        "onerror=alert(document.domain)&gt;"
    )

    response = await client.get(f"/api/emails/{sample_email.id}")

    assert response.status_code == 200
    body = response.json()["body"]
    assert "Safe text" in body
    assert "&lt;img" not in body
    assert "<img" not in body
    assert "onerror" not in body
    assert "alert(" not in body


@pytest.mark.asyncio
async def test_get_email_thread(client: AsyncClient, db_session, sample_email: Email):
    response = await client.get(f"/api/emails/thread/{sample_email.thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert "thread" in data
    assert len(data["thread"]) == 1
    assert data["thread"][0]["id"] == sample_email.id


@pytest.mark.asyncio
async def test_get_emails_only_returns_authenticated_user_rows(
    client: AsyncClient, db_session
):
    own_email = Email(
        id=1,
        user_id="testuser",
        message_id="msg-own",
        thread_id="thread-own",
        sender="owner@example.com",
        recipients="user@example.com",
        subject="Own Subject",
        date=datetime.datetime.now(datetime.timezone.utc),
        body="Own body.",
    )
    foreign_email = Email(
        id=2,
        user_id="other-user",
        message_id="msg-foreign",
        thread_id="thread-foreign",
        sender="other@example.com",
        recipients="user@example.com",
        subject="Foreign Subject",
        date=datetime.datetime.now(datetime.timezone.utc),
        body="Foreign body.",
    )
    db_session.items = [own_email, foreign_email]

    response = await client.get("/api/emails?limit=10")

    assert response.status_code == 200
    data = response.json()["emails"]
    assert [item["subject"] for item in data] == ["Own Subject"]


@pytest.mark.asyncio
async def test_get_emails_filters_by_mailbox_account_id(
    client: AsyncClient, db_session
):
    alpha_email = Email(
        id=1,
        user_id="testuser",
        mailbox_account_id=1,
        message_id="msg-alpha",
        thread_id="thread-alpha",
        sender="alpha@example.com",
        recipients="user@example.com",
        subject="Alpha Subject",
        date=datetime.datetime.now(datetime.timezone.utc),
        body="Alpha body.",
    )
    beta_email = Email(
        id=2,
        user_id="testuser",
        mailbox_account_id=2,
        message_id="msg-beta",
        thread_id="thread-beta",
        sender="beta@example.com",
        recipients="user@example.com",
        subject="Beta Subject",
        date=datetime.datetime.now(datetime.timezone.utc),
        body="Beta body.",
    )
    db_session.items = [alpha_email, beta_email]

    response = await client.get("/api/emails?limit=10&mailbox_account_id=2")

    assert response.status_code == 200
    data = response.json()["emails"]
    assert [item["subject"] for item in data] == ["Beta Subject"]


@pytest.mark.asyncio
async def test_get_emails_rejects_unowned_mailbox_account_id(
    client: AsyncClient, db_session
):
    db_session.mailbox_account_ids = {2}

    response = await client.get("/api/emails?limit=10&mailbox_account_id=1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Mailbox account not found"}


@pytest.mark.asyncio
async def test_get_email_by_id_rejects_foreign_owned_row(
    client: AsyncClient, db_session
):
    foreign_email = Email(
        id=2,
        user_id="other-user",
        message_id="msg-foreign",
        thread_id="thread-foreign",
        sender="other@example.com",
        recipients="user@example.com",
        subject="Foreign Subject",
        date=datetime.datetime.now(datetime.timezone.utc),
        body="Foreign body.",
    )
    db_session.items = [foreign_email]

    response = await client.get("/api/emails/2")

    assert response.status_code == 404


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
async def test_get_email_thread_respects_mailbox_account_filter(
    client: AsyncClient, db_session
):
    alpha = Email(
        id=1,
        user_id="testuser",
        mailbox_account_id=None,
        message_id="alpha-msg",
        thread_id="shared-thread",
        sender="alpha@example.com",
        recipients="user@example.com",
        subject="Alpha thread",
        date=datetime.datetime(2026, 4, 27, 10, 0, tzinfo=datetime.timezone.utc),
        body="Alpha body",
    )
    beta = Email(
        id=2,
        user_id="testuser",
        mailbox_account_id=2,
        message_id="beta-msg",
        thread_id="shared-thread",
        sender="beta@example.com",
        recipients="user@example.com",
        subject="Beta thread",
        date=datetime.datetime(2026, 4, 27, 11, 0, tzinfo=datetime.timezone.utc),
        body="Beta body",
    )
    db_session.items = [alpha, beta]

    response = await client.get("/api/emails/thread/shared-thread?mailbox_account_id=2")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["thread"]] == [1, 2]


@pytest.mark.asyncio
async def test_get_email_thread_rejects_unowned_mailbox_account_id(
    client: AsyncClient, db_session, sample_email: Email
):
    sample_email.mailbox_account_id = None
    db_session.mailbox_account_ids = {2}

    response = await client.get(
        f"/api/emails/thread/{sample_email.thread_id}?mailbox_account_id=1"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Mailbox account not found"}


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
    from api.emails import get_current_user as emails_get_current_user
    from db.session import get_db

    calls = []

    async def auth_override():
        calls.append("hit")
        return "authorized-user"

    app.dependency_overrides[emails_get_current_user] = auth_override
    original_get_db = app.dependency_overrides[get_db]

    async def authorized_db():
        session = original_get_db()
        session.items[0].user_id = "authorized-user"
        return session

    app.dependency_overrides[get_db] = authorized_db

    response = await client.get(path)

    assert response.status_code == 200
    assert calls == ["hit"]


@patch("api.emails.send_email", return_value={"status": "simulated", "simulated": True})
def test_send_email_endpoint(mock_send_email):
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app, headers=auth_headers("testuser"))

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
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_username="testuser",
        smtp_password=None,
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
        client = TestClient(app, headers=auth_headers("testuser"))
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


@patch("api.emails.send_email", return_value={"status": "simulated", "simulated": True})
def test_send_email_endpoint_prefers_default_mailbox_account(
    mock_send_email, sample_email
):
    from main import app
    from fastapi.testclient import TestClient
    from db.session import get_db

    class MailboxAccount:
        def __init__(self):
            self.smtp_server = "smtp.mailbox.example.com"
            self.smtp_port = 465
            self.smtp_username = "alpha@example.com"
            self.smtp_password = "mailbox-secret"

    class MailboxSession(MockSession):
        async def scalar(self, query):
            query_str = str(query).lower()
            if "from mailbox_accounts" in query_str:
                return MailboxAccount()
            return await super().scalar(query)

    async def mailbox_db():
        yield MailboxSession([sample_email])

    app.dependency_overrides[get_db] = mailbox_db
    try:
        client = TestClient(app, headers=auth_headers("testuser"))
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
        smtp_server="smtp.mailbox.example.com",
        smtp_port=465,
        smtp_username="alpha@example.com",
        smtp_password="mailbox-secret",
        in_reply_to=None,
        references=None,
    )


@patch("api.emails.send_email", return_value={"status": "failed", "simulated": False})
def test_send_email_endpoint_rejects_failed_send_status(mock_send_email):
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app, headers=auth_headers("testuser"))

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
