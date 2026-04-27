from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.llm_service import extract_todos_and_summary, draft_reply, ExtractionResult
from core.exceptions import LLMServiceError

router = APIRouter(prefix="/api/llm")

class SummarizeRequest(BaseModel):
    email_body: str

class DraftRequest(BaseModel):
    email_body: str
    instruction: str

@router.post("/summarize", response_model=ExtractionResult)
async def summarize_endpoint(request: SummarizeRequest):
    try:
        return await extract_todos_and_summary(request.email_body)
    except LLMServiceError:
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing the request.")
    except Exception:
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing the request.")

@router.post("/draft")
async def draft_endpoint(request: DraftRequest):
    try:
        reply = await draft_reply(request.email_body, request.instruction)
        return {"draft": reply}
    except LLMServiceError:
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing the request.")
    except Exception:
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing the request.")
