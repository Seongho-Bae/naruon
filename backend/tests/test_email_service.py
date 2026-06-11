import hashlib

from services.email_service import (
    detect_reply_tracking,
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

    def test_generate_email_fingerprint_long_body(self):
        long_body = "A" * 1000
        email_data = {
            "sender": "test@example.com",
            "subject": "Hello",
            "date": "2023-01-01T12:00:00",
            "body": long_body,
        }

        fingerprint = generate_email_fingerprint(email_data)

        raw_str = f"test@example.com|Hello|2023-01-01T12:00:00|{'A' * 500}"
        expected = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        assert fingerprint == expected

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

    def test_detect_reply_tracking_please_reply(self):
        assert detect_reply_tracking(
            {"body": "This is an important message, please reply soon."}
        ) is True

    def test_detect_reply_tracking_question_mark(self):
        assert detect_reply_tracking({"body": "How are you doing today?"}) is True

    def test_detect_reply_tracking_case_insensitive(self):
        assert detect_reply_tracking({"body": "Please Reply to this email."}) is True

    def test_detect_reply_tracking_no_match(self):
        assert detect_reply_tracking(
            {"body": "This is a standard statement without any tracking triggers."}
        ) is False

    def test_detect_reply_tracking_empty_body(self):
        assert detect_reply_tracking({}) is False

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
