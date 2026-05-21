import logging

import httpx
from openai import AsyncOpenAI
from core.config import settings
from core.exceptions import LLMServiceError
from pydantic import BaseModel
from services.llm_provider_urls import validate_llm_provider_base_url_async

logger = logging.getLogger(__name__)


class ExtractionResult(BaseModel):
    summary: str
    todos: list[str]
    provenance: str | None = None


async def extract_todos_and_summary(
    email_body: str,
    openai_api_key: str,
    base_url: str | None = None,
    provider_name: str = "OpenAI",
) -> ExtractionResult:
    if not openai_api_key:
        raise ValueError("API Key is not set")

    validated_base_url = await validate_llm_provider_base_url_async(base_url)
    client = AsyncOpenAI(
        api_key=openai_api_key,
        base_url=validated_base_url,
        http_client=httpx.AsyncClient(follow_redirects=False),
    )
    try:
        response = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Summarize the email and extract action items.",
                },
                {"role": "user", "content": email_body},
            ],
            response_format=ExtractionResult,
        )
    except Exception as e:
        logger.error(f"Error calling LLM API for extraction: {e}")
        raise LLMServiceError(f"LLM API error during extraction: {e}") from e
    finally:
        await client.close()

    parsed = response.choices[0].message.parsed
    if not parsed:
        raise RuntimeError("Failed to parse LLM response")

    parsed.provenance = f"{provider_name} ({settings.OPENAI_MODEL})"
    return parsed


async def draft_reply(
    email_body: str, instruction: str, openai_api_key: str, base_url: str | None = None
) -> str:
    if not openai_api_key:
        raise ValueError("API Key is not set")

    validated_base_url = await validate_llm_provider_base_url_async(base_url)
    client = AsyncOpenAI(
        api_key=openai_api_key,
        base_url=validated_base_url,
        http_client=httpx.AsyncClient(follow_redirects=False),
    )
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"You are drafting a professional reply. Instruction: {instruction}",
                },
                {"role": "user", "content": email_body},
            ],
        )
    except Exception as e:
        logger.error(f"Error calling LLM API for drafting: {e}")
        raise LLMServiceError(f"LLM API error during drafting: {e}") from e
    finally:
        await client.close()

    content = response.choices[0].message.content
    return content if content is not None else ""
