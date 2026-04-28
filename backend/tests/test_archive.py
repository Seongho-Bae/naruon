import os
import zipfile
import pytest
import asyncio
from pathlib import Path

from services.archive import extract_backup, extract_backup_async
from services.exceptions import (
    InvalidArchiveError,
    ArchiveSizeExceededError,
    ArchiveFileCountExceededError,
)


def test_extract_backup_success(tmp_path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("test.eml", b"Subject: Test Email")
        z.writestr("folder/", b"")
        z.writestr("folder/test2.eml", b"Subject: Test Email 2")

    out_dir = tmp_path / "output"
    extracted_files = extract_backup(zip_path, out_dir)

    # Check only files are returned, not directories
    assert len(extracted_files) == 2
    assert any(f.name == "test.eml" for f in extracted_files)
    assert any(f.name == "test2.eml" for f in extracted_files)
    assert not any(f.name == "folder" for f in extracted_files)

    for f in extracted_files:
        assert f.exists()
        assert f.is_file()


def test_extract_backup_file_not_found(tmp_path):
    with pytest.raises(InvalidArchiveError, match="Failed to extract archive"):
        extract_backup(tmp_path / "missing.zip", tmp_path / "output")


def test_extract_backup_bad_zip_file(tmp_path):
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_text("This is not a zip file")

    with pytest.raises(InvalidArchiveError, match="Failed to extract archive"):
        extract_backup(bad_zip, tmp_path / "output")


def test_extract_backup_size_exceeded(tmp_path, monkeypatch):
    import services.archive

    monkeypatch.setattr(services.archive, "MAX_EXTRACT_SIZE", 10)  # 10 bytes limit

    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("large.txt", b"A" * 20)  # 20 bytes

    with pytest.raises(
        ArchiveSizeExceededError,
        match="Archive exceeds maximum allowed extraction size",
    ):
        extract_backup(zip_path, tmp_path / "output")


def test_extract_backup_malformed_path(tmp_path):
    zip_path = tmp_path / "malformed.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        # Create a file with a relative path trying to escape directory
        z.writestr("../malformed.eml", b"Subject: Malformed Email")

    out_dir = tmp_path / "output"
    extracted_files = extract_backup(zip_path, out_dir)

    assert len(extracted_files) == 1
    assert extracted_files[0].name == "malformed.eml"
    assert ".." not in str(extracted_files[0])
    for f in extracted_files:
        assert f.exists()
        assert f.is_file()


def test_extract_backup_file_count_exceeded(tmp_path, monkeypatch):
    import services.archive

    monkeypatch.setattr(services.archive, "MAX_FILE_COUNT", 2)

    zip_path = tmp_path / "test_count.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("file1.txt", b"1")
        z.writestr("file2.txt", b"2")
        z.writestr("file3.txt", b"3")

    with pytest.raises(
        ArchiveFileCountExceededError,
        match="Archive exceeds maximum allowed file count",
    ):
        extract_backup(zip_path, tmp_path / "output")


def test_extract_backup_async(tmp_path):
    zip_path = tmp_path / "test_async.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("test.eml", b"Subject: Test Email")

    out_dir = tmp_path / "output"
    extracted_files = asyncio.run(extract_backup_async(zip_path, out_dir))

    assert len(extracted_files) == 1
    assert extracted_files[0].name == "test.eml"
    assert extracted_files[0].exists()
