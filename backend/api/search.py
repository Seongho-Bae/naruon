from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api")

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResponse(BaseModel):
    results: list[dict]

@router.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    # Minimal skeleton for now. Actual search will be implemented here.
    return SearchResponse(results=[])