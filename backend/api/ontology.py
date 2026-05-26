from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List

from db.session import get_db
from db.models import SenderRelationship
from api.auth import get_auth_context, AuthContext
from services.ontology_service import ontology_service

router = APIRouter(prefix="/api/ontology", tags=["ontology"])

class RelationshipResponse(BaseModel):
    sender_email: str
    relationship_type: str
    confidence_score: float
    next_action: str
    action_reason: str

class RelationshipCreate(BaseModel):
    sender_email: str
    relationship_type: str
    confidence_score: float = 1.0

@router.get("/relationships", response_model=List[RelationshipResponse])
async def get_relationships(
    auth_ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    user_id = auth_ctx.user_id
    stmt = select(SenderRelationship).where(SenderRelationship.user_id == user_id)
    result = await db.execute(stmt)
    rels = result.scalars().all()
    return [
        RelationshipResponse(
            sender_email=r.sender_email,
            relationship_type=r.relationship_type,
            confidence_score=r.confidence_score,
            **ontology_service.next_action_for_relationship(r.relationship_type),
        )
        for r in rels
    ]

@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship(
    req: RelationshipCreate,
    auth_ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    user_id = auth_ctx.user_id
    
    stmt = select(SenderRelationship).where(
        SenderRelationship.user_id == user_id,
        SenderRelationship.sender_email == req.sender_email
    )
    result = await db.execute(stmt)
    rel = result.scalars().first()
    
    if rel:
        rel.relationship_type = req.relationship_type
        rel.confidence_score = req.confidence_score
    else:
        rel = SenderRelationship(
            user_id=user_id,
            sender_email=req.sender_email,
            relationship_type=req.relationship_type,
            confidence_score=req.confidence_score
        )
        db.add(rel)
        
    await db.commit()
    await db.refresh(rel)
    
    return RelationshipResponse(
        sender_email=rel.sender_email,
        relationship_type=rel.relationship_type,
        confidence_score=rel.confidence_score,
        **ontology_service.next_action_for_relationship(rel.relationship_type),
    )
