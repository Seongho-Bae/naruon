import tempfile
import os
import datetime
import pytest
from services.email_parser import parse_eml
from services.exceptions import EmailParseError

def test_parse_eml_basic():
    eml_content = b"""Message-ID: <123@test.com>
From: test@test.com\x00
To: recipient@test.com
Subject: Hello\x00World
Date: Mon, 27 Apr 2026 10:00:00 +0000

This is a test email.\x00"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as f:
        f.write(eml_content)
        temp_path = f.name

    try:
        parsed = parse_eml(temp_path)
        assert parsed["message_id"] == "<123@test.com>"
        assert parsed["sender"] == "test@test.com"  # NUL removed
        assert parsed["subject"] == "HelloWorld"    # NUL removed
        assert "This is a test email." in parsed["body"]
        assert "\x00" not in parsed["body"]
    finally:
        os.unlink(temp_path)

def test_parse_eml_multipart_html_fallback():
    eml_content = b"""Message-ID: <multi@test.com>
From: multi@test.com
To: recipient@test.com
Subject: Multipart HTML
Date: Mon, 27 Apr 2026 10:00:00 +0000
Content-Type: multipart/alternative; boundary="boundary-string"

--boundary-string
Content-Type: text/html; charset="utf-8"

<p>This is HTML content</p>
--boundary-string--"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as f:
        f.write(eml_content)
        temp_path = f.name

    try:
        parsed = parse_eml(temp_path)
        assert "<p>This is HTML content</p>" in parsed["body"]
    finally:
        os.unlink(temp_path)

def test_parse_eml_missing_and_malformed_date():
    eml_content1 = b"""Message-ID: <nodate@test.com>
From: test@test.com
To: recipient@test.com
Subject: No Date

Test."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as f:
        f.write(eml_content1)
        temp_path1 = f.name

    eml_content2 = b"""Message-ID: <baddate@test.com>
From: test@test.com
To: recipient@test.com
Subject: Bad Date
Date: Invalid-Date-Format

Test."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as f:
        f.write(eml_content2)
        temp_path2 = f.name

    try:
        # Missing date
        parsed1 = parse_eml(temp_path1)
        assert isinstance(parsed1["date"], datetime.datetime)

        # Malformed date
        parsed2 = parse_eml(temp_path2)
        assert isinstance(parsed2["date"], datetime.datetime)
    finally:
        os.unlink(temp_path1)
        os.unlink(temp_path2)

def test_parse_eml_io_error():
    with pytest.raises(EmailParseError):
        parse_eml("/path/to/nonexistent/file.eml")
