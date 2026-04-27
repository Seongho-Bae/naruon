from fastapi import APIRouter
from pydantic import BaseModel
from services.llm_service import extract_todos_and_summary, draft_reply, ExtractionResult

router = APIRouter(prefix="/api/llm")

class SummarizeRequest(BaseModel):
    email_body: str

class DraftRequest(BaseModel):
    email_body: str
    instruction: str

@router.post("/summarize", response_model=ExtractionResult)
async def summarize_endpoint(request: SummarizeRequest):
    return await extract_todos_and_summary(request.email_body)

@router.post("/draft")
async def draft_endpoint(request: DraftRequest):
    reply = await draft_reply(request.email_body, request.instruction)
    return {"draft": reply}
