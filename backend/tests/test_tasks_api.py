import base64
import datetime
import hashlib
import hmac
import json
import os
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from api.auth import get_auth_context
from core.config import settings
from db.models import Email, TicketTask
from db.session import get_db
from main import app

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")
TEST_SESSION_HMAC_SECRET = os.environ["AUTH_SESSION_HMAC_SECRET"]


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _signed_session_token(payload: dict[str, object]) -> str:
    header_segment = _base64url_encode(
        json.dumps(
            {"alg": "HS256", "typ": "JWT"}, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    )
    payload_segment = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}"
    signature = hmac.new(
        TEST_SESSION_HMAC_SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def _valid_session_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "ver": 1,
        "iss": "naruon-control-plane",
        "aud": "naruon-api",
        "sub": "alice",
        "role": "organization_admin",
        "org": "org-acme",
        "groups": [],
        "workspace": "workspace-org-acme",
        "exp": int(time.time()) + 300,
    }
    payload.update(overrides)
    return payload


class MockTaskSession:
    def __init__(self) -> None:
        self.emails: dict[int, Email] = {}
        self.tasks: list[TicketTask] = []

    async def get(self, model, primary_key):
        if model is Email:
            return self.emails.get(primary_key)
        return None

    async def execute(self, stmt):
        descriptions = getattr(stmt, "column_descriptions", [])

        class MockScalars:
            def __init__(self, items):
                self._items = items

            def all(self):
                return self._items

        class MockResult:
            def __init__(self, items):
                self._items = items

            def scalars(self):
                return MockScalars(self._items)

            def all(self):
                return self._items

            def scalar_one_or_none(self):
                if not self._items:
                    return None
                if len(self._items) > 1:
                    raise AssertionError("Mock result expected at most one row")
                return self._items[0]

        if descriptions and descriptions[0].get("entity") is Email:
            params = stmt.compile().params
            source_email_id = params.get("message_id_1")
            user_id = params.get("user_id_1")
            organization_id = params.get("organization_id_1")
            return MockResult(
                [
                    email
                    for email in self.emails.values()
                    if email.message_id == source_email_id
                    and email.user_id == user_id
                    and email.organization_id == organization_id
                ]
            )

        if descriptions and descriptions[0].get("entity") is TicketTask:
            statement_text = str(stmt).lower()
            scoped_email_join = (
                "emails.user_id" in statement_text
                and "emails.organization_id" in statement_text
            )

            def source_message_id(task: TicketTask) -> str | None:
                if task.related_email_id is None:
                    return None
                source_email = self.emails.get(task.related_email_id)
                if source_email is None:
                    return None
                if scoped_email_join and (
                    source_email.user_id != task.user_id
                    or source_email.organization_id != task.organization_id
                ):
                    return None
                return source_email.message_id

            return MockResult([(task, source_message_id(task)) for task in self.tasks])

        return MockResult(self.tasks)

    def add(self, obj):
        if isinstance(obj, TicketTask):
            obj.id = len(self.tasks) + 1
            if not getattr(obj, "task_uid", None):
                obj.task_uid = uuid.uuid4().hex
            now = datetime.datetime.now(datetime.timezone.utc)
            obj.created_at = now
            obj.updated_at = now
            self.tasks.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


mock_session = MockTaskSession()


@pytest.fixture(autouse=True)
def override_get_db():
    app.dependency_overrides[get_db] = lambda: mock_session
    yield
    app.dependency_overrides.pop(get_db, None)
    mock_session.emails = {}
    mock_session.tasks = []


@pytest.fixture
def auth_client():
    with TestClient(
        app,
        headers={"X-User-Id": "alice", "X-Organization-Id": "org-acme"},
    ) as client:
        yield client


def test_create_ticket_tasks_accepts_signed_bearer_session():
    mock_session.emails[14] = make_email()
    app.dependency_overrides.pop(get_auth_context, None)
    previous_secret = settings.AUTH_SESSION_HMAC_SECRET
    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    token = _signed_session_token(_valid_session_payload())

    try:
        with TestClient(
            app,
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = client.post(
                "/api/tasks/from-email",
                json={
                    "source_email_id": "<message-14@example.com>",
                    "items": ["담당자 확인"],
                },
            )
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 1
    assert body["tasks"][0]["source_email_id"] == "<message-14@example.com>"
    assert "user_id" not in body["tasks"][0]
    assert "organization_id" not in body["tasks"][0]


def test_list_ticket_tasks_does_not_leak_cross_tenant_source_email(auth_client):
    now = datetime.datetime.now(datetime.timezone.utc)
    mock_session.emails[99] = make_email(
        email_id=99,
        user_id="bob",
        organization_id="org-rival",
        thread_id="thread-rival",
    )
    mock_session.tasks.append(
        TicketTask(
            id=1,
            task_uid="opaque-task-id",
            user_id="alice",
            organization_id="org-acme",
            title="교차 테넌트 소스 확인",
            status="open",
            priority="normal",
            source_type="email",
            related_email_id=99,
            related_thread_id="thread-rival",
            created_at=now,
            updated_at=now,
        )
    )

    response = auth_client.get("/api/tasks")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body[0]["id"] == "opaque-task-id"
    assert body[0]["source_email_id"] is None
    assert body[0]["related_thread_id"] is None


def make_email(
    *,
    email_id: int = 14,
    user_id: str = "alice",
    organization_id: str | None = "org-acme",
    thread_id: str | None = "thread-123",
) -> Email:
    return Email(
        id=email_id,
        user_id=user_id,
        organization_id=organization_id,
        message_id=f"<message-{email_id}@example.com>",
        thread_id=thread_id,
        sender="pm@example.com",
        recipients="alice@example.com",
        subject="Task source email",
        date=datetime.datetime(2026, 5, 19, tzinfo=datetime.timezone.utc),
        body="Please create tracked work items.",
    )


def test_ticket_task_database_columns_use_two_word_snake_case():
    column_names = {column.name for column in TicketTask.__table__.columns}

    assert column_names == {
        "task_id",
        "task_uid",
        "user_id",
        "organization_id",
        "task_title",
        "status_code",
        "priority_code",
        "source_type",
        "email_id",
        "thread_id",
        "created_at",
        "updated_at",
    }
    assert all("_" in column_name for column_name in column_names)


def test_create_ticket_tasks_from_email_links_source_email_and_thread(auth_client):
    mock_session.emails[14] = make_email()

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-14@example.com>",
            "thread_id": "thread-123",
            "items": ["담당자 확인", "일정 공유"],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 2
    assert [type(task["id"]) for task in body["tasks"]] == [str, str]
    assert [len(task["id"]) for task in body["tasks"]] == [32, 32]
    assert [task["title"] for task in body["tasks"]] == ["담당자 확인", "일정 공유"]
    assert {task["status"] for task in body["tasks"]} == {"open"}
    assert {task["priority"] for task in body["tasks"]} == {"normal"}
    assert {task["source_type"] for task in body["tasks"]} == {"email"}
    assert {task["source_email_id"] for task in body["tasks"]} == {
        "<message-14@example.com>"
    }
    assert all("related_email_id" not in task for task in body["tasks"])
    assert {task["related_thread_id"] for task in body["tasks"]} == {"thread-123"}
    assert all("user_id" not in task for task in body["tasks"])
    assert all("organization_id" not in task for task in body["tasks"])


def test_create_ticket_tasks_sanitizes_nul_bytes_from_execution_items(auth_client):
    mock_session.emails[14] = make_email()

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-14@example.com>",
            "thread_id": "thread-123",
            "items": ["담당자\u0000 확인"],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tasks"][0]["title"] == "담당자 확인"
    assert "\x00" not in mock_session.tasks[0].title


def test_create_ticket_tasks_rejects_html_execution_item_titles(auth_client):
    mock_session.emails[14] = make_email()

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-14@example.com>",
            "thread_id": "thread-123",
            "items": ["<script>alert('XSS by Strix');</script>"],
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Execution items must be plain text"}
    assert mock_session.tasks == []


@pytest.mark.parametrize(
    "payload",
    [
        "&lt;img src=x onerror=alert(document.domain)&gt;",
        "<!-- hidden task markup -->",
        "<!DOCTYPE html>",
        "<?xml version='1.0'?>",
        "< /script>alert(1)</script>",
        "<svg/onload=alert(1)@x>",
        "<math/href=javascript:alert(1)@x>",
        "<script src=//attacker.example/xss.js",
        "&lt;script src=//attacker.example/xss.js",
    ],
)
def test_create_ticket_tasks_rejects_encoded_and_malformed_html_titles(
    auth_client, payload
):
    mock_session.emails[14] = make_email()

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-14@example.com>",
            "thread_id": "thread-123",
            "items": [payload],
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Execution items must be plain text"}
    assert mock_session.tasks == []


def test_create_ticket_tasks_allows_plain_comparison_text(auth_client):
    mock_session.emails[14] = make_email()

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-14@example.com>",
            "thread_id": "thread-123",
            "items": ["Confirm 2 < 3 and 5 > 4"],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["tasks"][0]["title"] == "Confirm 2 < 3 and 5 > 4"


def test_create_ticket_tasks_allows_plain_alphabetic_comparison_text(auth_client):
    mock_session.emails[14] = make_email()

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-14@example.com>",
            "thread_id": "thread-123",
            "items": ["Compare a < b before saving"],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["tasks"][0]["title"] == "Compare a < b before saving"


def test_create_ticket_tasks_rejects_email_owned_by_another_member(auth_client):
    mock_session.emails[99] = make_email(
        email_id=99,
        user_id="bob",
        organization_id="org-acme",
        thread_id="thread-bob",
    )

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-99@example.com>",
            "thread_id": "thread-bob",
            "items": ["권한 밖 업무"],
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Source email not found"}
    assert mock_session.tasks == []


def test_create_ticket_tasks_rejects_empty_execution_items(auth_client):
    mock_session.emails[14] = make_email()

    response = auth_client.post(
        "/api/tasks/from-email",
        json={
            "source_email_id": "<message-14@example.com>",
            "thread_id": "thread-123",
            "items": [" "],
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "At least one execution item is required"}
    assert mock_session.tasks == []
