from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from db.session import get_db
from db.models import PromptTemplate, LLMProvider, TenantConfig
from api.auth import get_current_user
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

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
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class PromptTestRequest(BaseModel):
    content: str
    variables: dict[str, str]

class PromptTestResponse(BaseModel):
    result: str

async def execute_prompt_with_llm(prompt_text: str, api_key: str, base_url: Optional[str] = None) -> dict:
    from openai import AsyncOpenAI
    from core.config import settings
    
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content
        return {"result": content if content else ""}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Prompt execution failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to execute prompt with AI provider. Check provider status.")

@router.get("", response_model=List[PromptResponse])
async def list_prompts(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    # Only return prompts created by user OR shared prompts
    result = await db.execute(
        select(PromptTemplate).where(
            (PromptTemplate.created_by == user_id) | (PromptTemplate.is_shared == True)
        )
    )
    return result.scalars().all()

@router.post("", response_model=PromptResponse)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    prompt = PromptTemplate(
        title=data.title,
        description=data.description,
        content=data.content,
        is_shared=data.is_shared,
        created_by=user_id
    )
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt

@router.post("/test", response_model=PromptTestResponse)
async def test_prompt(
    data: PromptTestRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    # Substitute variables
    prompt_text = data.content
    for k, v in data.variables.items():
        prompt_text = prompt_text.replace(f"{{{{{k}}}}}", v)
        
    # Find active provider
    provider_result = await db.execute(select(LLMProvider).where(LLMProvider.is_active == True))
    active_provider = provider_result.scalars().first()
    
    api_key = None
    base_url = None
    
    if active_provider and active_provider.api_key:
        api_key = active_provider.api_key
        base_url = active_provider.base_url
    else:
        tenant_result = await db.execute(select(TenantConfig).where(TenantConfig.user_id == user_id))
        tenant_config = tenant_result.scalars().first()
        if tenant_config and tenant_config.openai_api_key:
            api_key = tenant_config.openai_api_key
            
    if not api_key:
        raise HTTPException(status_code=400, detail="LLM API key not configured")
        
    return await execute_prompt_with_llm(prompt_text, api_key, base_url)
