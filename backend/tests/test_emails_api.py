import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from db.models import Email
from main import app
import datetime


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class MockSession:
    def __init__(self, items):
        self.items = items

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
        return None


@pytest.fixture
def sample_email():
    return Email(
        id=1,
        message_id="msg123",
        sender="test@example.com",
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
async def test_get_email_by_id(client: AsyncClient, db_session, sample_email: Email):
    response = await client.get(f"/api/emails/{sample_email.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_email.id


from unittest.mock import patch


@patch("api.emails.send_email", return_value=True)
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
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    mock_send_email.assert_called_once_with(
        "test@example.com", "Re: Test", "This is a reply."
    )
