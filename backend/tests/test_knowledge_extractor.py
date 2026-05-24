import pytest
from db.models import Email
from services.knowledge_extractor import extract_knowledge_from_self_sent
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_extract_knowledge_from_self_sent():
    # Mock db session
    db = AsyncMock(spec=AsyncSession)
    
    # Mock self-sent email
    email = Email(
        id=1,
        user_id="testuser",
        organization_id=None,
        message_id="msg1",
        thread_id="thread1",
        sender="testuser@example.com",
        recipients="testuser@example.com",
        subject="Buy milk",
        body="Don't forget to buy milk later."
    )
    
    task = await extract_knowledge_from_self_sent(db, email)
    
    assert task is not None
    assert task.title == "[Memo] Buy milk"
    assert task.source_type == "email_auto_extract"
    assert task.related_email_id == 1
    assert task.related_thread_id == "thread1"
    
    # Verify it was added and committed
    db.add.assert_called_once_with(task)
    db.commit.assert_awaited_once()
