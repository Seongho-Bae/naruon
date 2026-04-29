import pytest
import datetime
from unittest.mock import patch, AsyncMock
from scripts.import_fixtures import process_zip_file
import import_fixtures


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
        def scalar_one_or_none(self):
            return None

    class MockSession:
        def __init__(self):
            self.added = None
            self.committed = False

        async def execute(self, _query):
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

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures, "generate_embeddings", new_callable=AsyncMock
    ) as mock_embeddings, patch.object(
        import_fixtures, "assign_thread_id", new_callable=AsyncMock
    ) as mock_assign:
        mock_embeddings.return_value = [[0.0] * 1536]
        mock_assign.return_value = "canonical-thread"

        imported = await import_fixtures.import_eml_file(session, eml_file)

    assert imported is True
    assert session.added.thread_id == "canonical-thread"
    assert session.committed is True


@pytest.mark.asyncio
async def test_root_importer_uses_local_embedding_without_openai_key(tmp_path, monkeypatch):
    class MockResult:
        def scalar_one_or_none(self):
            return None

    class MockSession:
        def __init__(self):
            self.added = None

        async def execute(self, _query):
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

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures, "generate_embeddings", side_effect=AssertionError("network call")
    ):
        imported = await import_fixtures.import_eml_file(session, eml_file)

    assert imported is True
    assert session.added.embedding == [0.0] * 1536


@pytest.mark.asyncio
async def test_root_importer_rolls_back_and_returns_false_on_commit_failure(tmp_path):
    class MockResult:
        def scalar_one_or_none(self):
            return None

    class MockSession:
        def __init__(self):
            self.added = None
            self.rolled_back = False

        async def execute(self, _query):
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

    with patch.object(import_fixtures, "parse_eml", return_value=parsed), patch.object(
        import_fixtures, "generate_embeddings", new_callable=AsyncMock
    ) as mock_embeddings, patch.object(
        import_fixtures, "assign_thread_id", new_callable=AsyncMock
    ) as mock_assign:
        mock_embeddings.return_value = [[0.0] * 1536]
        mock_assign.return_value = "commit-failure-thread"

        imported = await import_fixtures.import_eml_file(session, eml_file)

    assert imported is False
    assert session.added is not None
    assert session.rolled_back is True
