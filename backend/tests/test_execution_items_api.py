import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

from db.models import Email
from main import app


class MockResult:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows

    def scalar_one_or_none(self):
        return self.rows[0] if self.rows else None


class MockExecutionItem:
    def __init__(
        self,
        *,
        id: int,
        user_id: str,
        organization_id: str | None,
        workspace_id: str,
        source_mailbox_account_id: int | None,
        source_email_id: int | None,
        source_thread_id: str | None,
        source_message_id: str | None,
        source_snippet: str | None,
        title: str,
        sender: str,
        status: str,
        created_at: datetime.datetime,
        updated_at: datetime.datetime,
        completed_at: datetime.datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.organization_id = organization_id
        self.workspace_id = workspace_id
        self.source_mailbox_account_id = source_mailbox_account_id
        self.source_email_id = source_email_id
        self.source_thread_id = source_thread_id
        self.source_message_id = source_message_id
        self.source_snippet = source_snippet
        self.title = title
        self.sender = sender
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.completed_at = completed_at


class MockTenantConfig:
    def __init__(
        self,
        user_id: str,
        *,
        smtp_username: str | None = None,
        imap_username: str | None = None,
    ):
        self.user_id = user_id
        self.smtp_username = smtp_username
        self.imap_username = imap_username


class MockSession:
    def __init__(self, emails, execution_items, tenant_configs=None):
        self.emails = {email.id: email for email in emails}
        self.execution_items = execution_items
        self.tenant_configs = tenant_configs or {}
        self.next_id = max((item.id for item in execution_items), default=0) + 1
        self.commit_error: Exception | None = None

    async def execute(self, query):
        query_str = str(query).lower()
        params = query.compile().params

        if "from execution_items" in query_str:
            rows = list(self.execution_items)
            user_id = next(
                (value for key, value in params.items() if "user_id" in key), None
            )
            workspace_id = next(
                (value for key, value in params.items() if "workspace_id" in key), None
            )
            source_email_id = next(
                (value for key, value in params.items() if "source_email_id" in key),
                None,
            )
            item_id = next(
                (value for key, value in params.items() if key.startswith("id_")), None
            )
            if user_id is not None:
                rows = [row for row in rows if row.user_id == user_id]
            if workspace_id is not None:
                rows = [row for row in rows if row.workspace_id == workspace_id]
            if source_email_id is not None:
                rows = [row for row in rows if row.source_email_id == source_email_id]
            if item_id is not None:
                rows = [row for row in rows if row.id == item_id]
            rows = sorted(rows, key=lambda row: row.updated_at, reverse=True)
            return MockResult(rows)

        if "from emails" in query_str:
            user_id = next(
                (value for key, value in params.items() if "user_id" in key), None
            )
            item_id = next(
                (value for key, value in params.items() if key.startswith("id_")), None
            )
            rows = [self.emails[item_id]] if item_id in self.emails else []
            if user_id is not None:
                rows = [row for row in rows if getattr(row, "user_id", None) == user_id]
            return MockResult(rows)

        if "from tenant_configs" in query_str:
            user_id = next(
                (value for key, value in params.items() if "user_id" in key), None
            )
            rows = (
                [self.tenant_configs[user_id]] if user_id in self.tenant_configs else []
            )
            return MockResult(rows)

        return MockResult([])

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = self.next_id
            self.next_id += 1
        self.execution_items.append(obj)

    async def commit(self):
        if self.commit_error is not None:
            error = self.commit_error
            self.commit_error = None
            raise error
        return None

    async def refresh(self, obj):
        return None

    async def rollback(self):
        return None


@pytest.fixture
def sample_email():
    return Email(
        id=7,
        user_id="testuser",
        mailbox_account_id=2,
        message_id="<q2@example.com>",
        thread_id="thread-q2",
        sender="김지현 PM",
        reply_to="jihyun@naruon.ai",
        recipients="user@naruon.ai",
        subject="Q2 출시 계획 및 우선순위 조정",
        date=datetime.datetime(2026, 5, 11, 9, 30, tzinfo=datetime.timezone.utc),
        body="Q2 출시 일정과 마케팅 계획을 우선순위 기준으로 재정렬해 보았습니다.",
    )


@pytest.fixture
def db_session(sample_email):
    return MockSession(
        [sample_email],
        [
            MockExecutionItem(
                id=1,
                user_id="testuser",
                organization_id="org-acme",
                workspace_id="workspace-org-acme",
                source_mailbox_account_id=2,
                source_email_id=7,
                source_thread_id="thread-q2",
                source_message_id="<q2@example.com>",
                source_snippet="Q2 출시 일정과 마케팅 계획을 우선순위 기준으로 재정렬해 보았습니다.",
                title="Q2 출시 계획 및 우선순위 조정",
                sender="김지현 PM",
                status="queued",
                created_at=datetime.datetime(
                    2026, 5, 14, 9, 0, tzinfo=datetime.timezone.utc
                ),
                updated_at=datetime.datetime(
                    2026, 5, 14, 9, 5, tzinfo=datetime.timezone.utc
                ),
            ),
            MockExecutionItem(
                id=2,
                user_id="testuser",
                organization_id="org-beta",
                workspace_id="workspace-org-beta",
                source_mailbox_account_id=3,
                source_email_id=99,
                source_thread_id="thread-other",
                source_message_id="<other@example.com>",
                source_snippet="다른 사용자 실행 항목 근거",
                title="다른 사용자 실행 항목",
                sender="외부 사용자",
                status="queued",
                created_at=datetime.datetime(
                    2026, 5, 14, 9, 0, tzinfo=datetime.timezone.utc
                ),
                updated_at=datetime.datetime(
                    2026, 5, 14, 9, 6, tzinfo=datetime.timezone.utc
                ),
            ),
        ],
        tenant_configs={
            "testuser": MockTenantConfig(
                "testuser",
                smtp_username="user@naruon.ai",
                imap_username="user@naruon.ai",
            ),
        },
    )


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    from db.session import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_execution_items_returns_only_authenticated_user_items(
    client: AsyncClient,
):
    response = await client.get("/api/execution-items")

    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["user_id"] == "testuser"
    assert data[0]["organization_id"] == "org-acme"
    assert data[0]["source_mailbox_account_id"] == 2
    assert data[0]["source_snippet"].startswith("Q2 출시 일정")
    assert data[0]["title"] == "Q2 출시 계획 및 우선순위 조정"


@pytest.mark.asyncio
async def test_queue_execution_item_from_email_is_idempotent(
    client: AsyncClient, db_session: MockSession
):
    response = await client.post(
        "/api/execution-items/from-email", json={"email_id": 7}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["item"]["id"] == 1
    assert data["item"]["organization_id"] == "org-acme"
    assert data["item"]["source_mailbox_account_id"] == 2
    assert data["item"]["source_email_id"] == 7
    assert data["item"]["status"] == "queued"
    assert (
        len(
            [
                item
                for item in db_session.execution_items
                if item.user_id == "testuser" and item.organization_id == "org-acme"
            ]
        )
        == 1
    )


@pytest.mark.asyncio
async def test_patch_execution_item_marks_item_done_for_owner(
    client: AsyncClient, db_session: MockSession
):
    response = await client.patch("/api/execution-items/1", json={"status": "done"})

    assert response.status_code == 200
    data = response.json()["item"]
    assert data["status"] == "done"
    assert data["completed_at"] is not None
    assert db_session.execution_items[0].status == "done"


@pytest.mark.asyncio
async def test_patch_execution_item_rejects_cross_user_updates(client: AsyncClient):
    response = await client.patch("/api/execution-items/2", json={"status": "done"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_queue_execution_item_returns_404_for_missing_source_email(
    client: AsyncClient,
):
    response = await client.post(
        "/api/execution-items/from-email", json={"email_id": 404}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_queue_execution_item_rejects_email_outside_user_mailbox_scope(
    client: AsyncClient, db_session: MockSession, sample_email: Email
):
    db_session.emails[8] = Email(
        id=8,
        user_id="other-user",
        message_id="<foreign@example.com>",
        thread_id="thread-foreign",
        sender="outsider@example.com",
        reply_to="outsider@example.com",
        recipients="another@example.com",
        subject="타 사용자 메일",
        date=sample_email.date,
        body="foreign body",
    )

    response = await client.post(
        "/api/execution-items/from-email", json={"email_id": 8}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_execution_items_ignores_same_user_rows_from_other_organizations(
    client: AsyncClient,
):
    response = await client.get(
        "/api/execution-items",
        headers={"X-User-Id": "testuser", "X-Organization-Id": "org-acme"},
    )

    assert response.status_code == 200
    data = response.json()["items"]
    assert [item["id"] for item in data] == [1]


@pytest.mark.asyncio
async def test_queue_execution_item_handles_unique_race_by_returning_existing_item(
    client: AsyncClient, db_session: MockSession
):
    db_session.execution_items = []
    existing = MockExecutionItem(
        id=3,
        user_id="testuser",
        organization_id="org-acme",
        workspace_id="workspace-org-acme",
        source_mailbox_account_id=2,
        source_email_id=7,
        source_thread_id="thread-q2",
        source_message_id="<q2@example.com>",
        source_snippet="Q2 출시 일정과 마케팅 계획을 우선순위 기준으로 재정렬해 보았습니다.",
        title="Q2 출시 계획 및 우선순위 조정",
        sender="김지현 PM",
        status="queued",
        created_at=datetime.datetime(2026, 5, 14, 9, 0, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2026, 5, 14, 9, 5, tzinfo=datetime.timezone.utc),
    )
    db_session.commit_error = IntegrityError(
        "duplicate", params=None, orig=Exception("duplicate")
    )

    async def inject_existing_after_rollback():
        db_session.execution_items.append(existing)

    original_rollback = db_session.rollback

    async def rollback_with_insert():
        await original_rollback()
        await inject_existing_after_rollback()

    db_session.rollback = rollback_with_insert

    response = await client.post(
        "/api/execution-items/from-email", json={"email_id": 7}
    )

    assert response.status_code == 200
    assert response.json()["item"]["id"] == 3
