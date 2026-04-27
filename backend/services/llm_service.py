import logging
from openai import AsyncOpenAI
from core.config import settings
from core.exceptions import LLMServiceError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExtractionResult(BaseModel):
    summary: str
    todos: list[str]

_client: AsyncOpenAI | None = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
    return _client

async def extract_todos_and_summary(email_body: str) -> ExtractionResult:
    client = _get_client()
    try:
        response = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Summarize the email and extract action items."},
                {"role": "user", "content": email_body}
            ],
            response_format=ExtractionResult
        )
    except Exception as e:
        logger.error(f"Error calling OpenAI API for extraction: {e}")
        raise LLMServiceError(f"OpenAI API error during extraction: {e}") from e

    if not response.choices[0].message.parsed:
        raise RuntimeError("Failed to parse LLM response")
    return response.choices[0].message.parsed

async def draft_reply(email_body: str, instruction: str) -> str:
    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"You are drafting a professional reply. Instruction: {instruction}"},
                {"role": "user", "content": email_body}
            ]
        )
    except Exception as e:
        logger.error(f"Error calling OpenAI API for drafting: {e}")
        raise LLMServiceError(f"OpenAI API error during drafting: {e}") from e

    content = response.choices[0].message.content
    return content if content is not None else ""
