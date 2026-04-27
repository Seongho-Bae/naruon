import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings
from db.models import Base

@pytest.mark.asyncio
async def test_engine_creation():
    engine = create_async_engine(settings.DATABASE_URL)
    assert engine is not None
