import re

# 1. Update backend/services/llm_service.py
with open("backend/services/llm_service.py", "r") as f:
    content = f.read()

translate_fn = """
async def translate_email_body(
    email_body: str,
    target_language: str,
    openai_api_key: str,
    base_url: str | None = None,
    model: str | None = None,
) -> str:
    if not openai_api_key:
        raise ValueError("API Key is not set")

    configured_base_url = base_url if base_url is not None else settings.OPENAI_BASE_URL
    validated_base_url, http_client = await build_llm_provider_http_client(
        configured_base_url
    )
    selected_model = model or settings.OPENAI_MODEL
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an expert translator. Translate the given email body into {target_language}. "
                "Preserve the original tone, formatting, and any professional nuances. "
                "Output ONLY the translated text without any conversational fillers."
            ),
        },
        {"role": "user", "content": email_body},
    ]

    client = AsyncOpenAI(
        api_key=openai_api_key,
        base_url=validated_base_url,
        http_client=http_client,
    )
    try:
        response = await client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=0.3,
        )
    except Exception as e:
        logger.error(f"Error calling LLM API for translation: {e}")
        raise LLMServiceError(f"LLM API error during translation: {e}") from e
    finally:
        await client.close()

    content = response.choices[0].message.content
    return content if content is not None else ""

async def draft_reply(
"""
if "async def translate_email_body" not in content:
    content = content.replace("async def draft_reply(", translate_fn)
    with open("backend/services/llm_service.py", "w") as f:
        f.write(content)

# 2. Update backend/api/llm.py
with open("backend/api/llm.py", "r") as f:
    content = f.read()

if "TranslateRequest" not in content:
    content = content.replace(
        "draft_reply,\n    ExtractionResult,",
        "draft_reply,\n    translate_email_body,\n    ExtractionResult,"
    )

    req_class = """
class TranslateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_body: str = Field(min_length=1, max_length=LLM_EMAIL_BODY_MAX_CHARS)
    target_language: str = Field(min_length=1, max_length=50, default="Korean")

def _render_draft_reply_prompt(
"""
    content = content.replace("def _render_draft_reply_prompt(", req_class)

    translate_api = """
@router.post("/translate")
async def translate_endpoint(
    request: TranslateRequest,
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

        translation = await translate_email_body(
            request.email_body,
            request.target_language,
            runtime_provider.api_key,
            base_url=runtime_provider.base_url,
            model=runtime_provider.chat_model,
        )
        return {"translation": translation}
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

"""
    content = content + translate_api
    with open("backend/api/llm.py", "w") as f:
        f.write(content)
