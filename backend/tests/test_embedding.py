import pytest
import openai
from unittest.mock import patch, AsyncMock
from services.embedding import chunk_text, generate_embeddings
from services.exceptions import EmbeddingGenerationError


def test_chunk_text():
    text = "This is a long test string. " * 100
    chunks = chunk_text(text, chunk_size=50)
    assert len(chunks) > 1
    assert len(chunks[0]) <= 50


@pytest.mark.asyncio
async def test_generate_embeddings_success():
    with patch(
        "services.embedding.AsyncOpenAI"
    ) as mock_async_openai:
        mock_client = mock_async_openai.return_value
        mock_client.embeddings.create = AsyncMock()
        mock_response = AsyncMock()
        mock_data_1 = AsyncMock()
        mock_data_1.embedding = [0.1, 0.2, 0.3]
        mock_data_2 = AsyncMock()
        mock_data_2.embedding = [0.4, 0.5, 0.6]
        mock_response.data = [mock_data_1, mock_data_2]
        mock_client.embeddings.create.return_value = mock_response

        with patch("services.embedding.settings") as mock_settings:
            mock_settings.OPENAI_EMBEDDING_MODEL = "test-model"
            
            embeddings = await generate_embeddings(["test1", "test2"], "test-key")
            assert len(embeddings) == 2
            assert embeddings[0] == [0.1, 0.2, 0.3]
            assert embeddings[1] == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_generate_embeddings_api_error():
    with patch(
        "services.embedding.AsyncOpenAI"
    ) as mock_async_openai:
        mock_client = mock_async_openai.return_value
        mock_client.embeddings.create = AsyncMock(side_effect=openai.OpenAIError("API error"))

        with patch("services.embedding.settings") as mock_settings:
            mock_settings.OPENAI_EMBEDDING_MODEL = "test-model"
            
            with pytest.raises(EmbeddingGenerationError):
                await generate_embeddings(["test"], "test-key")


@pytest.mark.asyncio
async def test_generate_embeddings_missing_key():
    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        await generate_embeddings(["test"], "")
