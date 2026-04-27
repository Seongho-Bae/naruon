from openai import AsyncOpenAI
from core.config import settings
from pydantic import BaseModel

class ExtractionResult(BaseModel):
    summary: str
    todos: list[str]

async def _get_client() -> AsyncOpenAI:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())

async def extract_todos_and_summary(email_body: str) -> ExtractionResult:
    client = await _get_client()
    response = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Summarize the email and extract action items."},
            {"role": "user", "content": email_body}
        ],
        response_format=ExtractionResult
    )
    if not response.choices[0].message.parsed:
        raise RuntimeError("Failed to parse LLM response")
    return response.choices[0].message.parsed

async def draft_reply(email_body: str, instruction: str) -> str:
    client = await _get_client()
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"You are drafting a professional reply. Instruction: {instruction}"},
            {"role": "user", "content": email_body}
        ]
    )
    content = response.choices[0].message.content
    return content if content is not None else ""
