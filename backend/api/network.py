from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models import Email
from api.auth import get_current_user
import re

router = APIRouter(prefix="/api/network")


class Node(BaseModel):
    id: str
    label: str


class Edge(BaseModel):
    source: str
    target: str
    weight: int


class GraphResponse(BaseModel):
    nodes: list[Node]
    edges: list[Edge]


def extract_emails(text: str | None) -> list[str]:
    if not text:
        return []
    # simple email extraction regex
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    return re.findall(email_pattern, text)


@router.get("/graph", response_model=GraphResponse)
async def get_network_graph(
    limit: int = 500,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    if user_id and user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user_id = user_id or current_user

    result = await db.execute(
        select(Email.sender, Email.recipients)
        .where(Email.user_id == target_user_id)
        .limit(limit)
    )
    rows = result.fetchall()

    nodes_set = set()
    edges_dict = {}  # (sender, recipient) -> weight

    for row in rows:
        sender_str = row[0]
        recipients_str = row[1]

        senders = extract_emails(sender_str)
        recipients = extract_emails(recipients_str)

        sender_email = senders[0].lower() if senders else None

        if sender_email:
            nodes_set.add(sender_email)

        for rec in recipients:
            rec_email = rec.lower()
            nodes_set.add(rec_email)
            if sender_email and sender_email != rec_email:
                edge_key = (sender_email, rec_email)
                edges_dict[edge_key] = edges_dict.get(edge_key, 0) + 1

    nodes = [Node(id=email, label=email) for email in nodes_set]
    edges = [
        Edge(source=src, target=tgt, weight=weight)
        for (src, tgt), weight in edges_dict.items()
    ]

    return GraphResponse(nodes=nodes, edges=edges)
