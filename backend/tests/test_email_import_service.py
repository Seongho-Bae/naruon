from pathlib import Path
from unittest.mock import AsyncMock, Mock
import datetime

import pytest
from services import email_import_service
from services.email_import_service import _safe_item_filename, _safe_upload_filename

@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("file.zip", "file.zip"),
        ("", "upload"),
        (None, "upload"),
        ("/some/path/file.zip", "file.zip"),
        ("  spaced.zip  ", "spaced.zip"),
        ("/", "upload"),
    ]
)
def test_safe_upload_filename(input_name, expected):
    assert _safe_upload_filename(input_name) == expected

@pytest.mark.parametrize(
    "upload_name,eml_path,expected",
    [
        # without eml_path
        ("my_archive.zip", None, "my_archive.zip"),
        ("", None, "upload"),
        ("/path/to/my_archive.zip", None, "my_archive.zip"),

        # matching eml_path
        ("my_file.eml", Path("my_file.eml"), "my_file.eml"),
        ("/path/my_file.eml", Path("/other/path/my_file.eml"), "my_file.eml"),
        ("  my_file.eml  ", Path("my_file.eml"), "my_file.eml"),

        # differing eml_path
        ("my_archive.zip", Path("email_1.eml"), "my_archive.zip:email_1.eml"),
        ("/path/my_archive.zip", Path("/some/folder/email_1.eml"), "my_archive.zip:email_1.eml"),
        ("", Path("email_1.eml"), "upload:email_1.eml"),
    ]
)
def test_safe_item_filename(upload_name, eml_path, expected):
    assert _safe_item_filename(upload_name, eml_path) == expected


@pytest.mark.asyncio
async def test_import_single_eml_offloads_read_and_byte_parse(tmp_path, monkeypatch):
    eml_path = tmp_path / "message.eml"
    eml_path.write_bytes(b"unused")
    expected_content = b"Message-ID: <threaded@test.com>\n\nBody"
    to_thread_calls = []
    parse_inputs = []

    async def fake_to_thread(func, *args, **kwargs):
        to_thread_calls.append((func, args, kwargs))
        return func(*args, **kwargs)

    def fake_read(path):
        assert path == eml_path
        return expected_content

    def fake_parse(content):
        parse_inputs.append(content)
        return {
            "message_id": "<threaded@test.com>",
            "thread_id": "<threaded@test.com>",
            "sender": "sender@test.com",
            "reply_to": None,
            "recipients": "recipient@test.com",
            "subject": "Threaded import",
            "in_reply_to": None,
            "references": None,
            "date": datetime.datetime(2026, 6, 16, tzinfo=datetime.timezone.utc),
            "body": "Body",
            "attachments": [],
        }

    monkeypatch.setattr(email_import_service.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(email_import_service, "_read_eml_bytes", fake_read)
    monkeypatch.setattr(email_import_service, "parse_eml_bytes", fake_parse)
    monkeypatch.setattr(
        email_import_service, "_find_existing_email", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        email_import_service, "assign_thread_id", AsyncMock(return_value="thread-1")
    )

    session = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    result = await email_import_service._import_single_eml(
        session,
        eml_path=eml_path,
        display_filename="message.eml",
        user_id="user-1",
        organization_id="org-1",
    )

    assert result.status == "imported"
    assert parse_inputs == [expected_content]
    assert [call[0] for call in to_thread_calls] == [fake_read, fake_parse]
    assert to_thread_calls[0][1] == (eml_path,)
    assert to_thread_calls[1][1] == (expected_content,)
    session.add.assert_called_once()
    session.commit.assert_awaited_once()
