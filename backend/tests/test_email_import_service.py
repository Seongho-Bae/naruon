import pytest
from pathlib import Path
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
import services.email_import_service as email_import_module
from services.exceptions import EmailParseError


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
    assert email_import_module._safe_upload_filename(input_name) == expected


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
    assert email_import_module._safe_item_filename(upload_name, eml_path) == expected


@pytest.mark.asyncio
async def test_import_single_eml_offloads_read_and_parse(monkeypatch, tmp_path):
    eml_path = tmp_path / "message.eml"
    eml_path.write_bytes(b"From: a@example.com\nTo: b@example.com\n\nbody")
    session = AsyncMock(spec=AsyncSession)
    calls = []

    def fake_read_and_parse(path):
        calls.append(("read_and_parse", path))
        raise EmailParseError("boom")

    async def fake_to_thread(func, *args):
        calls.append(("to_thread", func, args))
        return func(*args)

    monkeypatch.setattr(
        email_import_module, "_read_and_parse_eml", fake_read_and_parse
    )
    monkeypatch.setattr(email_import_module.asyncio, "to_thread", fake_to_thread)

    result = await email_import_module._import_single_eml(
        session,
        eml_path=eml_path,
        display_filename="message.eml",
        user_id="user-1",
        organization_id="org-1",
    )

    assert result.status == "failed"
    assert result.reason_code == "parse_failed"
    assert calls == [
        ("to_thread", fake_read_and_parse, (eml_path,)),
        ("read_and_parse", eml_path),
    ]
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_eml_paths_for_upload_offloads_upload_write(monkeypatch, tmp_path):
    upload = email_import_module.EmailImportUpload(
        filename="message.eml",
        content=b"From: a@example.com\nTo: b@example.com\n\nbody",
    )
    calls = []

    async def fake_to_thread(func, *args):
        calls.append((func, args))
        return func(*args)

    monkeypatch.setattr(email_import_module.asyncio, "to_thread", fake_to_thread)

    eml_paths, failure_reason = await email_import_module._eml_paths_for_upload(
        upload=upload,
        upload_dir=tmp_path,
    )

    assert failure_reason is None
    assert eml_paths == [tmp_path / "message.eml"]
    assert len(calls) == 1
    assert getattr(calls[0][0], "__self__", None) == tmp_path / "message.eml"
    assert calls[0][1] == (upload.content,)
    assert (tmp_path / "message.eml").read_bytes() == upload.content


@pytest.mark.asyncio
async def test_eml_paths_for_upload_reports_write_failure(monkeypatch, tmp_path):
    upload = email_import_module.EmailImportUpload(
        filename="message.eml",
        content=b"not written",
    )

    async def fake_to_thread(func, *args):
        raise OSError("disk full")

    monkeypatch.setattr(email_import_module.asyncio, "to_thread", fake_to_thread)

    eml_paths, failure_reason = await email_import_module._eml_paths_for_upload(
        upload=upload,
        upload_dir=tmp_path,
    )

    assert eml_paths == []
    assert failure_reason == "file_write_failed"
    assert not (tmp_path / "message.eml").exists()


@pytest.mark.asyncio
async def test_import_single_eml_rejects_symlink(tmp_path):
    target_path = tmp_path / "target.txt"
    target_path.write_text("not an eml")
    symlink_path = tmp_path / "message.eml"
    symlink_path.symlink_to(target_path)
    session = AsyncMock(spec=AsyncSession)

    result = await email_import_module._import_single_eml(
        session,
        eml_path=symlink_path,
        display_filename="message.eml",
        user_id="user-1",
        organization_id="org-1",
    )

    assert result.status == "failed"
    assert result.reason_code == "parse_failed"
    session.execute.assert_not_called()
