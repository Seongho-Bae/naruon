from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from db.models import Email
from services.embedding import generate_embeddings

router = APIRouter(prefix="/api")

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResultItem(BaseModel):
    id: int
    subject: str | None
    sender: str
    snippet: str
    score: float

class SearchResponse(BaseModel):
    results: list[SearchResultItem]

@router.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    if not request.query.strip():
        return SearchResponse(results=[])

    try:
        embeddings = await generate_embeddings([request.query])
        query_embedding = embeddings[0]

        fts_score = func.ts_rank_cd(func.to_tsvector('english', Email.body), func.plainto_tsquery('english', request.query))
        vector_distance = Email.embedding.cosine_distance(query_embedding)
        hybrid_score = fts_score - vector_distance

        stmt = select(
            Email,
            hybrid_score.label("score")
        ).order_by(
            hybrid_score.desc()
        ).limit(request.limit)

        result = await db.execute(stmt)
        rows = result.all()

        search_results = []
        for row in rows:
            email = row.Email
            score = row.score
            snippet = email.body[:200] + "..." if len(email.body) > 200 else email.body
            
            search_results.append(SearchResultItem(
                id=email.id,
                subject=email.subject,
                sender=email.sender,
                snippet=snippet,
                score=float(score) if score is not None else 0.0
            ))

        return SearchResponse(results=search_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))