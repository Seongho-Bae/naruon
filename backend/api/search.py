from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, union_all
from db.session import get_db
from db.models import Email, Attachment, TenantConfig
from services.embedding import generate_embeddings
from api.auth import get_current_user

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
async def hybrid_search(request: SearchRequest, user_id: str | None = None, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    if user_id and user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user_id = user_id or current_user

    if not request.query.strip():
        return SearchResponse(results=[])

    try:
        tenant_config = await db.scalar(select(TenantConfig).where(TenantConfig.user_id == target_user_id))
        if not tenant_config or not tenant_config.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")
        
        openai_api_key = tenant_config.openai_api_key
        
        embeddings = await generate_embeddings([request.query], openai_api_key)
        query_embedding = embeddings[0]

        fts_score_email = func.ts_rank_cd(
            func.to_tsvector("english", Email.body),
            func.plainto_tsquery("english", request.query),
        )
        vector_distance_email = Email.embedding.cosine_distance(query_embedding)
        hybrid_score_email = fts_score_email - vector_distance_email

        stmt_email = select(
            Email.id,
            Email.subject,
            Email.sender,
            Email.body.label("content"),
            hybrid_score_email.label("score"),
        )

        fts_score_att = func.ts_rank_cd(
            func.to_tsvector("english", Attachment.content),
            func.plainto_tsquery("english", request.query),
        )
        vector_distance_att = Attachment.embedding.cosine_distance(query_embedding)
        hybrid_score_att = fts_score_att - vector_distance_att

        stmt_att = (
            select(
                Email.id,
                Email.subject,
                Email.sender,
                Attachment.content.label("content"),
                hybrid_score_att.label("score"),
            )
            .select_from(Attachment)
            .join(Email, Attachment.email_id == Email.id)
        )

        combined = union_all(stmt_email, stmt_att).cte("combined_search")

        stmt = (
            select(
                combined.c.id,
                combined.c.subject,
                combined.c.sender,
                combined.c.content,
                combined.c.score,
            )
            .order_by(combined.c.score.desc())
            .limit(request.limit * 2)
        )

        result = await db.execute(stmt)
        rows = result.all()

        search_results = []
        seen_ids = set()
        for row in rows:
            if row.id in seen_ids:
                continue
            seen_ids.add(row.id)

            score = row.score
            snippet_source = row.content or ""
            snippet = (
                snippet_source[:200] + "..."
                if len(snippet_source) > 200
                else snippet_source
            )

            search_results.append(
                SearchResultItem(
                    id=row.id,
                    subject=row.subject,
                    sender=row.sender,
                    snippet=snippet,
                    score=float(score) if score is not None else 0.0,
                )
            )

            if len(search_results) >= request.limit:
                break

        return SearchResponse(results=search_results)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
