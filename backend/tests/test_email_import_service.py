import pytest
from pathlib import Path
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
