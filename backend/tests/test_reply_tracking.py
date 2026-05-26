import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import datetime
from api.emails import EmailListItem
from db.models import Email, TenantConfig


@pytest.mark.asyncio
async def test_identifying_sent_emails_awaiting_replies():
    # Write a test for the background job service
    # that flags missing replies.
    from services.reply_tracking_service import check_missing_replies

    session_mock = AsyncMock()

    # Let's say we have one email sent 3 days ago expecting a reply,
    # and no replies are found in the thread.

    email_awaiting = Email(
        id=1,
        user_id="user_1",
        sender="my@email.com",
        recipients="other@email.com",
        date=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3),
        body="Please reply by tomorrow.",
        thread_id="thread_1",
    )

    # We mock the query returning this email
    execute_result = MagicMock()
    config_mock = TenantConfig(user_id="user_1", smtp_username="my@email.com")

    def side_effect(stmt):
        stmt_str = str(stmt)
        if "tenant_configs" in stmt_str:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = config_mock
            return mock_res
        elif "emails.sender = " in stmt_str and "emails.date > " in stmt_str:
            mock_res = MagicMock()
            mock_res.scalars.return_value.all.return_value = [email_awaiting]
            return mock_res
        else:
            mock_res = MagicMock()
            mock_res.scalars.return_value.first.return_value = None
            return mock_res

    session_mock.execute.side_effect = side_effect

    flagged_emails = await check_missing_replies(session_mock, "user_1", "org_1")

    # The background job should return a list of flagged emails or update DB.
    # We'll assert it returns the flagged email ID.
    assert len(flagged_emails) == 1
    assert flagged_emails[0].id == 1


@pytest.mark.asyncio
async def test_requires_reply_in_email_response():
    # Test that `requires_reply` and `schedule_conflict` are exposed in response
    item = EmailListItem(
        id=1,
        subject="Test",
        sender="sender@test.com",
        date=datetime.datetime.now(datetime.timezone.utc),
        snippet="Test",
        requires_reply=True,
        schedule_conflict=False,
    )
    assert item.requires_reply is True
    assert item.schedule_conflict is False
