import os
import zipfile
import tempfile
from services.archive import extract_backup

def test_extract_backup():
    # Create a dummy zip file
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "test.zip")
        with zipfile.ZipFile(zip_path, 'w') as z:
            z.writestr("test.eml", b"Subject: Test Email")
        
        out_dir = os.path.join(tmpdir, "output")
        extracted_files = extract_backup(zip_path, out_dir)
        
        assert len(extracted_files) == 1
        assert extracted_files[0].endswith("test.eml")
        assert os.path.exists(extracted_files[0])
