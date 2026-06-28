import hashlib

from services.email_service import (
    generate_email_fingerprint,
    process_self_to_self,
)


class TestEmailService:
    def test_generate_email_fingerprint_basic(self):
        email_data = {
            "sender": "test@example.com",
            "subject": "Hello",
            "date": "2023-01-01T12:00:00",
            "body": "This is a test body.",
        }

        fingerprint = generate_email_fingerprint(email_data)

        raw_str = "test@example.com|Hello|2023-01-01T12:00:00|This is a test body."
        expected = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        assert fingerprint == expected

    def test_generate_email_fingerprint_long_body_uses_full_content(self):
        long_body = "A" * 1000
        email_data = {
            "sender": "test@example.com",
            "subject": "Hello",
            "date": "2023-01-01T12:00:00",
            "body": long_body,
        }

        fingerprint = generate_email_fingerprint(email_data)

        raw_str = f"test@example.com|Hello|2023-01-01T12:00:00|{'A' * 1000}"
        expected = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        assert fingerprint == expected

    def test_generate_email_fingerprint_long_body_differs_beyond_500_chars(self):
        prefix = "A" * 500
        email_data_1 = {
            "sender": "test@example.com",
            "subject": "Hello",
            "date": "2023-01-01T12:00:00",
            "body": prefix + "Unique content 1",
        }
        email_data_2 = {
            "sender": "test@example.com",
            "subject": "Hello",
            "date": "2023-01-01T12:00:00",
            "body": prefix + "Unique content 2",
        }

        fp1 = generate_email_fingerprint(email_data_1)
        fp2 = generate_email_fingerprint(email_data_2)
        assert fp1 != fp2, "Emails with different content beyond 500 chars must produce different fingerprints"

    def test_generate_email_fingerprint_empty_dict(self):
        fingerprint = generate_email_fingerprint({})

        expected = hashlib.sha256("|||".encode("utf-8")).hexdigest()
        assert fingerprint == expected

    def test_generate_email_fingerprint_missing_fields(self):
        email_data = {
            "sender": "test@example.com",
            "body": "Body only.",
        }

        fingerprint = generate_email_fingerprint(email_data)

        expected = hashlib.sha256(
            "test@example.com|||Body only.".encode("utf-8")
        ).hexdigest()
        assert fingerprint == expected

    def test_generate_email_fingerprint_identical_data(self):
        email_data = {
            "sender": "test@example.com",
            "subject": "Hello",
            "date": "2023-01-01",
            "body": "Test",
        }

        assert generate_email_fingerprint(email_data) == generate_email_fingerprint(
            email_data.copy()
        )

    def test_process_self_to_self_basic(self):
        email_data = {
            "sender": "user@example.com",
            "recipients": ["user@example.com"],
        }

        assert process_self_to_self(email_data, "user@example.com") is True

    def test_process_self_to_self_with_names(self):
        email_data = {
            "sender": "User Name <User@Example.com>",
            "recipients": ["User Name <user@example.com>"],
        }

        assert process_self_to_self(email_data, "user@example.com") is True

    def test_process_self_to_self_multiple_recipients(self):
        email_data = {
            "sender": "user@example.com",
            "recipients": ["other@example.com", "user@example.com"],
        }

        assert process_self_to_self(email_data, "user@example.com") is True

    def test_process_self_to_self_not_self(self):
        email_data = {
            "sender": "user@example.com",
            "recipients": ["other@example.com"],
        }

        assert process_self_to_self(email_data, "user@example.com") is False

    def test_process_self_to_self_sender_not_user(self):
        email_data = {
            "sender": "other@example.com",
            "recipients": ["user@example.com"],
        }

        assert process_self_to_self(email_data, "user@example.com") is False

    def test_process_self_to_self_string_recipient(self):
        email_data = {
            "sender": "user@example.com",
            "recipients": "user@example.com",
        }

        assert process_self_to_self(email_data, "user@example.com") is True

    def test_process_self_to_self_empty_fields(self):
        assert process_self_to_self({}, "user@example.com") is False

    def test_process_self_to_self_empty_user(self):
        email_data = {
            "sender": "user@example.com",
            "recipients": ["user@example.com"],
        }

        assert process_self_to_self(email_data, "") is False

    def test_process_self_to_self_invalid_emails(self):
        email_data = {
            "sender": "invalid-email",
            "recipients": ["another-invalid"],
        }

        assert process_self_to_self(email_data, "invalid-email") is False

    def test_process_self_to_self_unicode_homoglyph_rejected(self):
        """Cyrillic homoglyph addresses must not bypass self-to-self detection (CWE-178)."""
        cyrillic_sender = "u\u0455er@example.com"  # Cyrillic 'ѕ'
        email_data = {
            "sender": cyrillic_sender,
            "recipients": ["user@example.com"],
        }

        assert process_self_to_self(email_data, "user@example.com") is False
