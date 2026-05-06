import pytest
from sqlalchemy import UniqueConstraint, text
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings
from db.models import Email


def test_email_message_id_is_unique_per_user_not_global():
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in Email.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert Email.__table__.c.message_id.unique is not True
    assert ("user_id", "message_id") in unique_columns


@pytest.mark.asyncio
async def test_engine_creation():
    engine = create_async_engine(settings.DATABASE_URL)
    assert engine is not None

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
