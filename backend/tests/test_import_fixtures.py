import pytest
import datetime
from dataclasses import dataclass
from unittest.mock import patch, AsyncMock
from scripts.import_fixtures import process_zip_file
import import_fixtures
from core.config import settings


@pytest.mark.asyncio
async def test_process_zip_file():
    with patch("scripts.import_fixtures.extract_backup_async") as mock_extract:
        with patch("scripts.import_fixtures.parse_eml"):
            with patch("scripts.import_fixtures.generate_embeddings"):
                mock_extract.return_value = []
                # Ensure it doesn't crash on an empty zip
                await process_zip_file("dummy.zip", AsyncMock())


@pytest.mark.asyncio
async def test_root_importer_persists_canonical_thread_id(tmp_path):
    class MockResult:
        def __init__(self, scalar=None, rows=None):
            self._scalar = scalar
            self._rows = rows or []

        def scalar_one_or_none(self):
            return self._scalar

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class MockSession:
        def __init__(self):
            self.added = None
            self.committed = False

        async def execute(self, query):
            query_str = str(query).lower()
            if "from mailbox_accounts" in query_str:
                return MockResult(rows=[])
            return MockResult()

        def add(self, obj):
            self.added = obj

        async def commit(self):
            self.committed = True

    eml_file = tmp_path / "reply.eml"
    eml_file.write_text("Message-ID: <reply@example.com>\n\nBody")
    parsed = {
        "message_id": "<reply@example.com>",
        "sender": "sender@example.com",
        "recipients": "user@example.com",
        "subject": "Re: Root",
        "in_reply_to": "<parent@example.com>",
        "references": "<root@example.com> <parent@example.com>",
        "date": datetime.datetime.now(datetime.timezone.utc),
        "body": "Body",
        "attachments": [],
    }
    session = MockSession()
    previous_owner = settings.LEGACY_EMAIL_OWNER_USER_ID
    settings.LEGACY_EMAIL_OWNER_USER_ID = "testuser"

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures, "generate_embeddings", new_callable=AsyncMock
    ) as mock_embeddings, patch.object(
        import_fixtures, "assign_thread_id", new_callable=AsyncMock
    ) as mock_assign:
        mock_embeddings.return_value = [[0.0] * 1536]
        mock_assign.return_value = "canonical-thread"

        imported = await import_fixtures.import_eml_file(session, eml_file)

    settings.LEGACY_EMAIL_OWNER_USER_ID = previous_owner

    assert imported is True
    assert session.added is not None
    assert session.added.user_id == "testuser"
    assert session.added.thread_id == "canonical-thread"
    assert session.committed is True


@pytest.mark.asyncio
async def test_root_importer_uses_local_embedding_without_openai_key(
    tmp_path, monkeypatch
):
    class MockResult:
        def __init__(self, scalar=None, rows=None):
            self._scalar = scalar
            self._rows = rows or []

        def scalar_one_or_none(self):
            return self._scalar

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class MockSession:
        def __init__(self):
            self.added = None

        async def execute(self, query):
            query_str = str(query).lower()
            if "from mailbox_accounts" in query_str:
                return MockResult(rows=[])
            return MockResult()

        def add(self, obj):
            self.added = obj

        async def commit(self):
            pass

    eml_file = tmp_path / "root.eml"
    eml_file.write_text("Message-ID: <root@example.com>\n\nBody")
    parsed = {
        "message_id": "<root@example.com>",
        "sender": "sender@example.com",
        "recipients": "user@example.com",
        "subject": "Root",
        "date": datetime.datetime.now(datetime.timezone.utc),
        "body": "Body",
        "attachments": [],
    }
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = MockSession()
    previous_owner = settings.LEGACY_EMAIL_OWNER_USER_ID
    settings.LEGACY_EMAIL_OWNER_USER_ID = "testuser"

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures,
        "generate_embeddings",
        side_effect=AssertionError("network call"),
    ):
        imported = await import_fixtures.import_eml_file(session, eml_file)

    settings.LEGACY_EMAIL_OWNER_USER_ID = previous_owner

    assert imported is True
    assert session.added is not None
    assert session.added.embedding == [0.0] * 1536


@pytest.mark.asyncio
async def test_root_importer_rolls_back_and_returns_false_on_commit_failure(tmp_path):
    class MockResult:
        def __init__(self, scalar=None, rows=None):
            self._scalar = scalar
            self._rows = rows or []

        def scalar_one_or_none(self):
            return self._scalar

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class MockSession:
        def __init__(self):
            self.added = None
            self.rolled_back = False

        async def execute(self, query):
            query_str = str(query).lower()
            if "from mailbox_accounts" in query_str:
                return MockResult(rows=[])
            return MockResult()

        def add(self, obj):
            self.added = obj

        async def commit(self):
            raise RuntimeError("commit failed")

        async def rollback(self):
            self.rolled_back = True

    eml_file = tmp_path / "commit-failure.eml"
    eml_file.write_text("Message-ID: <commit-failure@example.com>\n\nBody")
    parsed = {
        "message_id": "<commit-failure@example.com>",
        "sender": "sender@example.com",
        "recipients": "user@example.com",
        "subject": "Commit failure",
        "date": datetime.datetime.now(datetime.timezone.utc),
        "body": "Body",
        "attachments": [],
    }
    session = MockSession()
    previous_owner = settings.LEGACY_EMAIL_OWNER_USER_ID
    settings.LEGACY_EMAIL_OWNER_USER_ID = "testuser"

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures, "generate_embeddings", new_callable=AsyncMock
    ) as mock_embeddings, patch.object(
        import_fixtures, "assign_thread_id", new_callable=AsyncMock
    ) as mock_assign:
        mock_embeddings.return_value = [[0.0] * 1536]
        mock_assign.return_value = "commit-failure-thread"

        imported = await import_fixtures.import_eml_file(session, eml_file)

    settings.LEGACY_EMAIL_OWNER_USER_ID = previous_owner

    assert imported is False
    assert session.added is not None
    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_root_importer_requires_explicit_owner(tmp_path):
    class MockResult:
        def scalar_one_or_none(self):
            return None

    class MockSession:
        async def execute(self, _query):
            return MockResult()

    eml_file = tmp_path / "missing-owner.eml"
    eml_file.write_text("Message-ID: <missing-owner@example.com>\n\nBody")

    previous_owner = settings.LEGACY_EMAIL_OWNER_USER_ID
    settings.LEGACY_EMAIL_OWNER_USER_ID = None
    imported = await import_fixtures.import_eml_file(MockSession(), eml_file)
    settings.LEGACY_EMAIL_OWNER_USER_ID = previous_owner

    assert imported is False


@pytest.mark.asyncio
async def test_root_importer_assigns_mailbox_account_id_from_matching_account(tmp_path):
    class MockResult:
        def __init__(self, scalar=None, rows=None):
            self._scalar = scalar
            self._rows = rows or []

        def scalar_one_or_none(self):
            return self._scalar

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class MailboxAccount:
        def __init__(self):
            self.id = 5
            self.email_address = "beta@example.com"
            self.smtp_username = "beta@example.com"
            self.imap_username = "beta@example.com"
            self.is_default_reply = True
            self.is_active = True

    class MockSession:
        def __init__(self):
            self.added = None

        async def execute(self, query):
            query_str = str(query).lower()
            if "from mailbox_accounts" in query_str:
                return MockResult(rows=[MailboxAccount()])
            return MockResult()

        def add(self, obj):
            self.added = obj

        async def commit(self):
            pass

    eml_file = tmp_path / "matching-mailbox.eml"
    eml_file.write_text("Message-ID: <matching@example.com>\n\nBody")
    parsed = {
        "message_id": "<matching@example.com>",
        "sender": "outside@example.com",
        "recipients": "beta@example.com",
        "subject": "Matching mailbox",
        "date": datetime.datetime.now(datetime.timezone.utc),
        "body": "Body",
        "attachments": [],
    }
    session = MockSession()
    previous_owner = settings.LEGACY_EMAIL_OWNER_USER_ID
    settings.LEGACY_EMAIL_OWNER_USER_ID = "testuser"

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures, "generate_embeddings", new_callable=AsyncMock
    ) as mock_embeddings, patch.object(
        import_fixtures, "assign_thread_id", new_callable=AsyncMock
    ) as mock_assign:
        mock_embeddings.return_value = [[0.0] * 1536]
        mock_assign.return_value = "matching-thread"

        imported = await import_fixtures.import_eml_file(session, eml_file)

    settings.LEGACY_EMAIL_OWNER_USER_ID = previous_owner

    assert imported is True
    assert session.added is not None
    assert session.added.mailbox_account_id == 5


@pytest.mark.asyncio
async def test_root_importer_upgrades_legacy_null_mailbox_row_when_match_is_found(
    tmp_path,
):
    class MockResult:
        def __init__(self, scalar=None, rows=None):
            self._scalar = scalar
            self._rows = rows or []

        def scalar_one_or_none(self):
            return self._scalar

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class MailboxAccount:
        def __init__(self):
            self.id = 5
            self.email_address = "beta@example.com"
            self.smtp_username = "beta@example.com"
            self.imap_username = "beta@example.com"
            self.is_default_reply = True
            self.is_active = True

    @dataclass
    class LegacyEmail:
        mailbox_account_id: int | None = None
        sender: str = "outside@example.com"
        reply_to: str | None = None
        recipients: str = "beta@example.com"
        subject: str = "Matching mailbox"
        in_reply_to: str | None = None
        references: str | None = None
        date: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        body: str = "Old body"
        embedding: list[float] | None = None
        thread_id: str = "legacy-thread"

    legacy_email = LegacyEmail()

    class MockSession:
        def __init__(self):
            self.commit_count = 0

        async def execute(self, query):
            query_str = str(query).lower()
            if "from mailbox_accounts" in query_str:
                return MockResult(rows=[MailboxAccount()])
            if "mailbox_account_id is null" in query_str:
                return MockResult(scalar=legacy_email)
            return MockResult()

        async def commit(self):
            self.commit_count += 1

    eml_file = tmp_path / "upgrade-legacy.eml"
    eml_file.write_text("Message-ID: <matching@example.com>\n\nBody")
    parsed = {
        "message_id": "<matching@example.com>",
        "sender": "outside@example.com",
        "recipients": "beta@example.com",
        "subject": "Matching mailbox",
        "date": datetime.datetime.now(datetime.timezone.utc),
        "body": "Body",
        "attachments": [],
    }
    session = MockSession()
    previous_owner = settings.LEGACY_EMAIL_OWNER_USER_ID
    settings.LEGACY_EMAIL_OWNER_USER_ID = "testuser"

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures, "generate_embeddings", new_callable=AsyncMock
    ) as mock_embeddings, patch.object(
        import_fixtures, "assign_thread_id", new_callable=AsyncMock
    ) as mock_assign:
        mock_embeddings.return_value = [[0.0] * 1536]
        mock_assign.return_value = "matching-thread"
        imported = await import_fixtures.import_eml_file(session, eml_file)

    settings.LEGACY_EMAIL_OWNER_USER_ID = previous_owner

    assert imported is True
    assert legacy_email.mailbox_account_id == 5
    assert legacy_email.thread_id == "matching-thread"
    assert session.commit_count == 1
