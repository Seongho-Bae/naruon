import pytest
from pathlib import Path
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from services import email_import_service
from services.email_import_service import (
    _read_and_parse_eml,
    _import_single_eml,
    _safe_item_filename,
    _safe_upload_filename,
)

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
async def test_import_single_eml_rejects_symlink(tmp_path):
    target_path = tmp_path / "target.txt"
    target_path.write_text("not an eml")
    symlink_path = tmp_path / "message.eml"
    symlink_path.symlink_to(target_path)
    session = AsyncMock(spec=AsyncSession)

    result = await _import_single_eml(
        session,
        eml_path=symlink_path,
        display_filename="message.eml",
        user_id="user-1",
        organization_id="org-1",
    )

    assert result.status == "failed"
    assert result.reason_code == "parse_failed"
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_import_single_eml_offloads_secure_read_and_parse(monkeypatch, tmp_path):
    eml_path = tmp_path / "message.eml"
    eml_path.write_bytes(b"From: sender@example.com\n\nbody")
    session = AsyncMock(spec=AsyncSession)
    to_thread_calls = []

    async def fake_to_thread(func, *args):
        to_thread_calls.append((func, args))
        raise email_import_service.EmailParseError("stop before database work")

    monkeypatch.setattr(email_import_service.asyncio, "to_thread", fake_to_thread)

    result = await _import_single_eml(
        session,
        eml_path=eml_path,
        display_filename="message.eml",
        user_id="user-1",
        organization_id="org-1",
    )

    assert result.status == "failed"
    assert result.reason_code == "parse_failed"
    assert to_thread_calls == [(_read_and_parse_eml, (eml_path,))]
    session.execute.assert_not_called()
