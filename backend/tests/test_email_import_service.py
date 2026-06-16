import pytest
from pathlib import Path
from services.email_import_service import (
    _import_single_eml,
    _safe_item_filename,
    _safe_upload_filename,
)


class DummySession:
    pass

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

    result = await _import_single_eml(
        DummySession(),
        eml_path=symlink_path,
        display_filename="message.eml",
        user_id="user-1",
        organization_id="org-1",
    )

    assert result.status == "failed"
    assert result.reason_code == "parse_failed"
