import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.llm_service import (
    extract_todos_and_summary,
    draft_reply,
    ExtractionResult,
)
from core.exceptions import LLMServiceError


@pytest.fixture
def mock_openai():
    with patch("services.llm_service._get_client") as mock_get_client:
        # Mock the AsyncOpenAI client instance
        mock_client_instance = MagicMock()
        mock_get_client.return_value = mock_client_instance
        yield mock_client_instance


@pytest.fixture(autouse=True)
def reset_client():
    # Reset the global client in llm_service before each test
    import services.llm_service

    services.llm_service._client = None
    yield


@pytest.mark.asyncio
async def test_extract_todos_and_summary_success(mock_openai):
    # Setup mock response
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.parsed = ExtractionResult(summary="Test summary", todos=["Task 1"])
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_openai.beta.chat.completions.parse = AsyncMock(return_value=mock_response)

    # Call the service
    result = await extract_todos_and_summary("Test email", "test-key")

    # Verify results
    assert result.summary == "Test summary"
    assert result.todos == ["Task 1"]
    mock_openai.beta.chat.completions.parse.assert_called_once()


@pytest.mark.asyncio
async def test_extract_todos_and_summary_api_error(mock_openai):
    # Setup mock to raise an exception
    mock_openai.beta.chat.completions.parse = AsyncMock(
        side_effect=Exception("API Error")
    )

    with pytest.raises(LLMServiceError, match="OpenAI API error during extraction"):
        await extract_todos_and_summary("Test email", "test-key")


@pytest.mark.asyncio
async def test_draft_reply_success(mock_openai):
    # Setup mock response
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Drafted reply text"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    # Call the service
    result = await draft_reply("Test email", "Draft a positive reply", "test-key")

    # Verify results
    assert result == "Drafted reply text"
    mock_openai.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_draft_reply_api_error(mock_openai):
    # Setup mock to raise an exception
    mock_openai.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    with pytest.raises(LLMServiceError, match="OpenAI API error during drafting"):
        await draft_reply("Test email", "Draft a positive reply", "test-key")
