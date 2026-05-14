import datetime
import socket

import pytest
from fastapi.testclient import TestClient

from db.session import get_db
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


class MockMailboxAccount:
    def __init__(
        self,
        *,
        id: int,
        user_id: str,
        email_address: str,
        display_name: str | None,
        provider: str,
        is_default_reply: bool,
        is_active: bool,
        smtp_server: str | None = None,
        smtp_port: int | None = None,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        imap_server: str | None = None,
        imap_port: int | None = None,
        imap_username: str | None = None,
        imap_password: str | None = None,
        pop3_server: str | None = None,
        pop3_port: int | None = None,
        pop3_username: str | None = None,
        pop3_password: str | None = None,
        updated_at: datetime.datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.email_address = email_address
        self.display_name = display_name
        self.provider = provider
        self.is_default_reply = is_default_reply
        self.is_active = is_active
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.imap_username = imap_username
        self.imap_password = imap_password
        self.pop3_server = pop3_server
        self.pop3_port = pop3_port
        self.pop3_username = pop3_username
        self.pop3_password = pop3_password
        self.created_at = updated_at or datetime.datetime.now(datetime.timezone.utc)
        self.updated_at = updated_at or datetime.datetime.now(datetime.timezone.utc)


class MockSession:
    def __init__(self, accounts=None):
        self.accounts = accounts or []
        self.next_id = max((item.id for item in self.accounts), default=0) + 1
        self.commit_error: Exception | None = None

    async def execute(self, query):
        params = query.compile().params
        query_str = str(query).lower()
        rows = list(self.accounts)
        if "from mailbox_accounts" in query_str:
            user_id = next(
                (value for key, value in params.items() if "user_id" in key), None
            )
            account_id = next(
                (value for key, value in params.items() if key.startswith("id_")), None
            )
            email_address = next(
                (value for key, value in params.items() if "email_address" in key), None
            )
            if user_id is not None:
                rows = [row for row in rows if row.user_id == user_id]
            if account_id is not None:
                rows = [row for row in rows if row.id == account_id]
            if email_address is not None:
                rows = [row for row in rows if row.email_address == email_address]
            rows = sorted(rows, key=lambda row: row.updated_at, reverse=True)
        else:
            rows = []
        return MockResult(rows)

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = self.next_id
            self.next_id += 1
        self.accounts.append(obj)

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
def mock_db():
    return MockSession(
        [
            MockMailboxAccount(
                id=1,
                user_id="testuser",
                email_address="alpha@example.com",
                display_name="Alpha",
                provider="custom",
                is_default_reply=True,
                is_active=True,
                smtp_server="smtp.example.com",
                smtp_port=587,
                smtp_username="alpha@example.com",
                smtp_password="smtp-secret",
                imap_server="imap.example.com",
                imap_port=993,
                imap_username="alpha@example.com",
                imap_password="imap-secret",
                pop3_server="pop.example.com",
                pop3_port=995,
                pop3_username="alpha@example.com",
                pop3_password="pop-secret",
            ),
            MockMailboxAccount(
                id=2,
                user_id="other-user",
                email_address="other@example.com",
                display_name="Other",
                provider="custom",
                is_default_reply=True,
                is_active=True,
            ),
        ]
    )


@pytest.fixture
def client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c
    app.dependency_overrides.clear()


def test_mailbox_accounts_are_listed_for_current_user_only(client):
    response = client.get("/api/mailbox-accounts")

    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 1
    assert data[0]["email_address"] == "alpha@example.com"
    assert data[0]["smtp_password_set"] is True
    assert data[0]["imap_password_set"] is True
    assert data[0]["pop3_server"] == "pop.example.com"
    assert data[0]["pop3_password_set"] is True


def test_mailbox_account_create_adds_new_account_and_demotes_existing_default(
    client, mock_db
):
    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "beta@example.com",
            "display_name": "Beta",
            "provider": "custom",
            "is_default_reply": True,
            "smtp_server": "smtp.beta.example.com",
            "smtp_port": 587,
            "smtp_username": "beta@example.com",
            "smtp_password": "smtp-beta",
            "imap_server": "imap.beta.example.com",
            "imap_port": 993,
            "imap_username": "beta@example.com",
            "imap_password": "imap-beta",
            "pop3_server": "pop.beta.example.com",
            "pop3_port": 995,
            "pop3_username": "beta@example.com",
            "pop3_password": "pop-beta",
        },
    )

    assert response.status_code == 200
    data = response.json()["item"]
    assert data["email_address"] == "beta@example.com"
    assert data["pop3_server"] == "pop.beta.example.com"
    assert data["pop3_password_set"] is True
    current_user_accounts = [
        item for item in mock_db.accounts if item.user_id == "testuser"
    ]
    assert len(current_user_accounts) == 2
    assert [item.is_default_reply for item in current_user_accounts] == [False, True]


def test_mailbox_account_create_forces_default_reply_accounts_active(client):
    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "gamma@example.com",
            "display_name": "Gamma",
            "provider": "custom",
            "is_default_reply": True,
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["item"]["is_default_reply"] is True
    assert response.json()["item"]["is_active"] is True


def test_mailbox_account_patch_is_self_owned(client, mock_db):
    response = client.patch(
        "/api/mailbox-accounts/1",
        json={"display_name": "Alpha Updated", "is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["item"]["display_name"] == "Alpha Updated"
    assert mock_db.accounts[0].is_active is False


def test_mailbox_account_patch_updates_email_address_for_owner(client, mock_db):
    response = client.patch(
        "/api/mailbox-accounts/1", json={"email_address": "renamed@example.com"}
    )

    assert response.status_code == 200
    assert response.json()["item"]["email_address"] == "renamed@example.com"
    assert mock_db.accounts[0].email_address == "renamed@example.com"


def test_mailbox_account_patch_forces_default_reply_accounts_active(client, mock_db):
    mock_db.accounts[0].is_default_reply = False
    mock_db.accounts[0].is_active = False

    response = client.patch(
        "/api/mailbox-accounts/1", json={"is_default_reply": True, "is_active": False}
    )

    assert response.status_code == 200
    assert response.json()["item"]["is_default_reply"] is True
    assert response.json()["item"]["is_active"] is True


def test_mailbox_account_create_sanitizes_nul_characters(client):
    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "nul@example.com",
            "display_name": "Bad\u0000Name",
            "provider": "custom",
            "smtp_username": "nul\u0000user@example.com",
            "smtp_password": "pass\u0000word",
        },
    )

    assert response.status_code == 200
    data = response.json()["item"]
    assert data["display_name"] == "BadName"
    assert data["smtp_username"] == "nuluser@example.com"


def test_mailbox_account_create_normalizes_email_and_rejects_partial_pop3_config(
    client,
):
    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "  padded@example.com  ",
            "display_name": " Padded ",
            "provider": "custom",
            "pop3_server": "pop.example.com",
        },
    )

    assert response.status_code == 400
    assert "POP3 서버와 포트는 함께 설정해야 합니다." in response.json()["detail"]


@pytest.mark.parametrize(
    ("field", "host", "port"),
    [
        ("smtp", "127.0.0.1", 587),
        ("smtp", "100.64.0.1", 587),
        ("imap", "localhost", 993),
        ("pop3", "169.254.169.254", 995),
    ],
)
def test_mailbox_account_create_rejects_internal_mail_server_hosts(
    client,
    field,
    host,
    port,
):
    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": f"{field}@example.com",
            "display_name": field.upper(),
            "provider": "custom",
            f"{field}_server": host,
            f"{field}_port": port,
        },
    )

    assert response.status_code == 400
    assert (
        "메일 서버 주소는 내부 네트워크를 사용할 수 없습니다."
        in response.json()["detail"]
    )


def test_mailbox_account_create_rejects_hosts_that_resolve_to_private_ips(
    client,
    monkeypatch,
):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        assert host == "mail.internal.example.com"
        assert port == 993
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("10.0.0.5", port),
            )
        ]

    monkeypatch.setattr(
        "services.mail_server_security.socket.getaddrinfo", fake_getaddrinfo
    )

    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "resolved-private@example.com",
            "display_name": "Resolved private",
            "provider": "custom",
            "imap_server": "mail.internal.example.com",
            "imap_port": 993,
        },
    )

    assert response.status_code == 400
    assert (
        "메일 서버 주소는 내부 네트워크를 사용할 수 없습니다."
        in response.json()["detail"]
    )


def test_mailbox_account_create_rejects_unsafe_mail_server_ports(client):
    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "ssh@example.com",
            "display_name": "SSH",
            "provider": "custom",
            "smtp_server": "smtp.example.com",
            "smtp_port": 22,
        },
    )

    assert response.status_code == 400
    assert (
        "SMTP 포트는 허용된 메일 포트만 사용할 수 있습니다."
        in response.json()["detail"]
    )


def test_mailbox_account_create_returns_conflict_for_duplicate_email_address(
    client, mock_db
):
    from sqlalchemy.exc import IntegrityError

    mock_db.commit_error = IntegrityError(
        "duplicate", params=None, orig=Exception("duplicate")
    )

    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "alpha@example.com",
            "display_name": "Alpha 2",
            "provider": "custom",
        },
    )

    assert response.status_code == 409


def test_mailbox_account_create_returns_503_when_encryption_key_is_missing(
    client, mock_db
):
    mock_db.commit_error = Exception("ENCRYPTION_KEY is required to encrypt secrets")

    response = client.post(
        "/api/mailbox-accounts",
        json={
            "email_address": "secure@example.com",
            "display_name": "Secure",
            "provider": "custom",
            "smtp_password": "secret",
        },
    )

    assert response.status_code == 503
    assert "Server encryption key is not configured" in response.json()["detail"]


def test_mailbox_account_make_default_is_self_owned(client, mock_db):
    mock_db.accounts.append(
        MockMailboxAccount(
            id=3,
            user_id="testuser",
            email_address="beta@example.com",
            display_name="Beta",
            provider="custom",
            is_default_reply=False,
            is_active=True,
        )
    )

    response = client.post("/api/mailbox-accounts/3/make-default-reply")

    assert response.status_code == 200
    assert mock_db.accounts[0].is_default_reply is False
    assert mock_db.accounts[-1].is_default_reply is True


def test_mailbox_account_endpoints_reject_cross_user_access(client):
    response = client.patch("/api/mailbox-accounts/2", json={"display_name": "Nope"})
    assert response.status_code == 404

    response = client.post("/api/mailbox-accounts/2/make-default-reply")
    assert response.status_code == 404
