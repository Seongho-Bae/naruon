import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.config import settings
from core.exceptions import LLMServiceError
from services.llm_service import (
    extract_todos_and_summary,
    draft_reply,
    ExtractionResult,
)


@pytest.fixture
def mock_openai():
    with patch("services.llm_service.AsyncOpenAI") as mock_async_openai:
        # Mock the AsyncOpenAI client instance
        mock_client_instance = MagicMock()
        mock_async_openai.return_value = mock_client_instance
        yield mock_client_instance


# Removed reset_client fixture


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

    with pytest.raises(LLMServiceError, match="LLM API error during extraction"):
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
async def test_draft_reply_resolves_custom_base_url_off_event_loop(
    mock_openai, monkeypatch
):
    monkeypatch.setattr(
        settings, "ALLOWED_LLM_BASE_URL_HOSTS", "llm-gateway.example.com"
    )

    def fake_getaddrinfo(host, port, type=0):
        assert host == "llm-gateway.example.com"
        assert port == 443
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise AssertionError("LLM provider DNS resolution ran on event loop")
        return [(2, 1, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(
        "services.llm_provider_urls.socket.getaddrinfo", fake_getaddrinfo
    )
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Drafted reply text"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await draft_reply(
        "Test email",
        "Draft a positive reply",
        "test-key",
        base_url="https://llm-gateway.example.com/v1",
    )

    assert result == "Drafted reply text"
    mock_openai.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_draft_reply_api_error(mock_openai):
    # Setup mock to raise an exception
    mock_openai.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    with pytest.raises(LLMServiceError, match="LLM API error during drafting"):
        await draft_reply("Test email", "Draft a positive reply", "test-key")
