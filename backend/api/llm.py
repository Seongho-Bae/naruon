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
from services.tenant_config_scope import get_scoped_tenant_config

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
        tenant_config = await get_scoped_tenant_config(
            db,
            target_user_id,
            auth_context.organization_id,
        )
        if not tenant_config or not tenant_config.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")

        openai_api_key = tenant_config.openai_api_key
        return await extract_todos_and_summary(request.email_body, openai_api_key)
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
        tenant_config = await get_scoped_tenant_config(
            db,
            target_user_id,
            auth_context.organization_id,
        )
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
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing the request.",
        )
