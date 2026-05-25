from unittest.mock import AsyncMock, patch
import pytest
from services.threading_service import generate_email_fingerprint
from db.models import Email

def test_generate_email_fingerprint():
    fingerprint1 = generate_email_fingerprint(
        subject="Test Subject",
        date_str="2023-10-27T10:00:00+00:00",
        sender="sender@example.com",
        recipient="receiver@example.com"
    )
    fingerprint2 = generate_email_fingerprint(
        subject="Test Subject",
        date_str="2023-10-27T10:00:00+00:00",
        sender="sender@example.com",
        recipient="receiver@example.com"
    )
    assert fingerprint1 == fingerprint2
    assert isinstance(fingerprint1, str)
    assert len(fingerprint1) > 0

    fingerprint3 = generate_email_fingerprint(
        subject="Other Subject",
        date_str="2023-10-27T10:00:00+00:00",
        sender="sender@example.com",
        recipient="receiver@example.com"
    )
    assert fingerprint1 != fingerprint3

@pytest.mark.asyncio
async def test_email_deduplication():
    from services.imap_worker import process_fetched_email
    from unittest.mock import MagicMock
    
    from services.email_parser import EmailData
    
    from datetime import datetime, timezone
    
    session_mock = AsyncMock()
    session_mock.add = MagicMock()
    # Assume select returns nothing (no duplicate)
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    session_mock.execute.return_value = execute_result
    
    email_data: EmailData = {
        "subject": "Test Duplicate",
        "date": datetime(2023, 10, 27, 10, 0, tzinfo=timezone.utc),
        "sender": "sender@example.com",
        "recipients": "receiver@example.com",
        "body": "Hello World",
        "message_id": "<msg1>",
        "in_reply_to": None,
        "references": None,
        "thread_id": None,
        "reply_to": None,
        "attachments": []
    }
    
    await process_fetched_email(session_mock, email_data, "user_1", "org_1")
    
    # Check that session.add was called since it's not a duplicate
    session_mock.add.assert_called_once()
    
    # Now simulate a duplicate
    session_mock.reset_mock()
    existing_email = Email(id=1, thread_id="thread_1")
    execute_result.scalar_one_or_none.return_value = existing_email
    
    await process_fetched_email(session_mock, email_data, "user_1", "org_1")
    
    # Check that session.add was NOT called, but existing_email's thread_id remains the same
    # or some update happens
    session_mock.add.assert_not_called()

