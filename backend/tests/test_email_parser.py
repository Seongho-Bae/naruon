from services.email_parser import parse_eml
import tempfile
import os

def test_parse_eml():
    eml_content = b"""Message-ID: <123@test.com>
From: test@test.com
To: recipient@test.com
Subject: Hello
Date: Mon, 27 Apr 2026 10:00:00 +0000

This is a test email."""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".eml") as f:
        f.write(eml_content)
        temp_path = f.name

    try:
        parsed = parse_eml(temp_path)
        assert parsed["message_id"] == "<123@test.com>"
        assert parsed["sender"] == "test@test.com"
        assert parsed["subject"] == "Hello"
        assert "This is a test email." in parsed["body"]
    finally:
        os.unlink(temp_path)
