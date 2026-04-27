from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI
from core.config import settings

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    actual_overlap = min(chunk_overlap, chunk_size // 2)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=actual_overlap,
        length_function=len,
    )
    return splitter.split_text(text)

async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    # Note: OPENAI_API_KEY is a SecretStr, so use .get_secret_value()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [data.embedding for data in response.data]
