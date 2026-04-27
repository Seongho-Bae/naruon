import os
import zipfile
import pytest
from pathlib import Path

from services.archive import extract_backup
from services.exceptions import InvalidArchiveError, ArchiveSizeExceededError

def test_extract_backup_success(tmp_path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as z:
        z.writestr("test.eml", b"Subject: Test Email")
        z.writestr("folder/", b"")
        z.writestr("folder/test2.eml", b"Subject: Test Email 2")
    
    out_dir = tmp_path / "output"
    extracted_files = extract_backup(zip_path, out_dir)
    
    # Check only files are returned, not directories
    assert len(extracted_files) == 2
    assert any(f.endswith("test.eml") for f in extracted_files)
    assert any(f.endswith("test2.eml") for f in extracted_files)
    assert not any(f.endswith("folder/") for f in extracted_files)
    
    for f in extracted_files:
        assert os.path.exists(f)
        assert os.path.isfile(f)

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
    monkeypatch.setattr(services.archive, "MAX_EXTRACT_SIZE", 10) # 10 bytes limit
    
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as z:
        z.writestr("large.txt", b"A" * 20) # 20 bytes
    
    with pytest.raises(ArchiveSizeExceededError, match="Archive exceeds maximum allowed extraction size"):
        extract_backup(zip_path, tmp_path / "output")
