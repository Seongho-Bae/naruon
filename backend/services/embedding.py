import openai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI
from core.config import settings
from services.exceptions import EmbeddingGenerationError


def chunk_text(
    text: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> list[str]:
    actual_overlap = min(chunk_overlap, chunk_size // 2)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=actual_overlap,
        length_function=len,
    )
    return splitter.split_text(text)


async def generate_embeddings(texts: list[str], openai_api_key: str) -> list[list[float]]:
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    
    # Instantiate client locally to avoid global state race conditions across tenants
    client = AsyncOpenAI(api_key=openai_api_key)

    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL, input=texts
        )
        return [data.embedding for data in response.data]
    except openai.OpenAIError as e:
        raise EmbeddingGenerationError(f"Failed to generate embeddings: {str(e)}")
