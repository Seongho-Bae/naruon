from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from db.session import get_db
from api.auth import AuthContext, get_auth_context
from services.llm_service import (
    extract_todos_and_summary,
    draft_reply,
    ExtractionResult,
)
from core.exceptions import LLMServiceError
from services.llm_provider_selection import resolve_runtime_llm_provider

router = APIRouter(prefix="/api/llm")


class SummarizeRequest(BaseModel):
    email_body: str


class DraftRequest(BaseModel):
    email_body: str
    instruction: str


@router.post("/summarize", response_model=ExtractionResult)
async def summarize_endpoint(
    request: SummarizeRequest,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    if user_id and user_id != auth_context.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user_id = user_id or auth_context.user_id

    try:
        runtime_provider = await resolve_runtime_llm_provider(
            db,
            user_id=target_user_id,
            organization_id=auth_context.organization_id,
        )
        if runtime_provider is None:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")

        return await extract_todos_and_summary(
            request.email_body,
            runtime_provider.api_key,
            base_url=runtime_provider.base_url,
            provider_name=runtime_provider.provider_name,
            model=runtime_provider.chat_model,
        )
    except LLMServiceError:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )


@router.post("/draft")
async def draft_endpoint(
    request: DraftRequest,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    if user_id and user_id != auth_context.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user_id = user_id or auth_context.user_id

    try:
        runtime_provider = await resolve_runtime_llm_provider(
            db,
            user_id=target_user_id,
            organization_id=auth_context.organization_id,
        )
        if runtime_provider is None:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")

        reply = await draft_reply(
            request.email_body,
            request.instruction,
            runtime_provider.api_key,
            base_url=runtime_provider.base_url,
            model=runtime_provider.chat_model,
        )
        return {"draft": reply}
    except LLMServiceError:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )
