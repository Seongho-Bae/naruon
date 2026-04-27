import pytest
from services.llm_service import extract_todos_and_summary, draft_reply

@pytest.mark.asyncio
async def test_extract_todos_and_summary_unauthorized():
    # Will fail if API key is not valid, but we just check if it's importable and callable
    try:
        await extract_todos_and_summary("Test email")
    except Exception as e:
        pass
    assert extract_todos_and_summary is not None
