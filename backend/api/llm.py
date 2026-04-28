from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from db.session import get_db
from db.models import TenantConfig
from services.llm_service import (
    extract_todos_and_summary,
    draft_reply,
    ExtractionResult,
)
from core.exceptions import LLMServiceError

router = APIRouter(prefix="/api/llm")


class SummarizeRequest(BaseModel):
    email_body: str


class DraftRequest(BaseModel):
    email_body: str
    instruction: str


@router.post("/summarize", response_model=ExtractionResult)
async def summarize_endpoint(request: SummarizeRequest, user_id: str | None = None, db: AsyncSession = Depends(get_db)):
    # TODO: Add Depends(get_current_user)
    try:
        tenant_config = await db.scalar(select(TenantConfig).where(TenantConfig.user_id == (user_id or "default")))
        if not tenant_config or not tenant_config.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")
            
        openai_api_key = tenant_config.openai_api_key
        return await extract_todos_and_summary(request.email_body, openai_api_key)
    except LLMServiceError:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )


@router.post("/draft")
async def draft_endpoint(request: DraftRequest, user_id: str | None = None, db: AsyncSession = Depends(get_db)):
    # TODO: Add Depends(get_current_user)
    try:
        tenant_config = await db.scalar(select(TenantConfig).where(TenantConfig.user_id == (user_id or "default")))
        if not tenant_config or not tenant_config.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")
            
        openai_api_key = tenant_config.openai_api_key
        reply = await draft_reply(request.email_body, request.instruction, openai_api_key)
        return {"draft": reply}
    except LLMServiceError:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )
