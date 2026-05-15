from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from typing import List, Optional
from db.session import get_db
from db.models import PromptTemplate, LLMProvider
from api.auth import AuthContext, get_auth_context
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

WORKSPACE_ADMIN_ROLES = {"platform_admin", "organization_admin"}


class PromptCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    is_shared: bool = False


class PromptResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content: str
    is_shared: bool
    created_by: str
    organization_id: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class PromptTestRequest(BaseModel):
    content: str
    variables: dict[str, str]


class PromptTestResponse(BaseModel):
    result: str


async def execute_prompt_with_llm(
    prompt_text: str, api_key: str, base_url: Optional[str] = None
) -> dict:
    from openai import AsyncOpenAI
    from core.config import settings

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.0,
        )
        content = response.choices[0].message.content
        return {"result": content if content else ""}
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Prompt execution failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to execute prompt with AI provider. Check provider status.",
        )


def build_prompt_list_statement(auth_context: AuthContext):
    owned_prompt = PromptTemplate.created_by == auth_context.user_id
    if not auth_context.organization_id:
        return select(PromptTemplate).where(owned_prompt)

    shared_in_org = and_(
        PromptTemplate.is_shared.is_(True),
        PromptTemplate.organization_id == auth_context.organization_id,
    )
    return select(PromptTemplate).where(or_(owned_prompt, shared_in_org))


def require_workspace_admin(auth_context: AuthContext, detail: str) -> None:
    if auth_context.role not in WORKSPACE_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail=detail)


def remove_nul_bytes(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.replace("\x00", "")


@router.get("", response_model=List[PromptResponse])
async def list_prompts(
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    # Return prompts created by user OR org-shared prompts in the same org only.
    result = await db.execute(build_prompt_list_statement(auth_context))
    return result.scalars().all()


@router.post("", response_model=PromptResponse)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    if data.is_shared and not auth_context.organization_id:
        raise HTTPException(
            status_code=400, detail="Shared prompts require organization scope"
        )
    if data.is_shared:
        require_workspace_admin(
            auth_context,
            "Workspace admin role is required for shared prompts",
        )

    prompt = PromptTemplate(
        title=remove_nul_bytes(data.title),
        description=remove_nul_bytes(data.description),
        content=remove_nul_bytes(data.content),
        is_shared=data.is_shared,
        created_by=auth_context.user_id,
        organization_id=auth_context.organization_id,
    )
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.post("/test", response_model=PromptTestResponse)
async def test_prompt(
    data: PromptTestRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    require_workspace_admin(
        auth_context,
        "Workspace admin role is required for prompt testing",
    )
    if not auth_context.organization_id:
        raise HTTPException(status_code=400, detail="LLM API key not configured")

    # Find active provider in the authenticated organization only.
    provider_result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.organization_id == auth_context.organization_id,
            LLMProvider.is_active.is_(True),
        )
    )
    active_provider = provider_result.scalars().first()

    api_key = None
    base_url = None

    if active_provider and active_provider.api_key:
        api_key = active_provider.api_key
        base_url = active_provider.base_url

    if not api_key:
        raise HTTPException(status_code=400, detail="LLM API key not configured")

    # Substitute variables only after authorization and provider validation.
    prompt_text = remove_nul_bytes(data.content) or ""
    for k, v in data.variables.items():
        prompt_text = prompt_text.replace(f"{{{{{k}}}}}", remove_nul_bytes(v) or "")

    return await execute_prompt_with_llm(prompt_text, api_key, base_url)
