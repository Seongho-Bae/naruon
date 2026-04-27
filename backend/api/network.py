from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models import Email
import re

router = APIRouter(prefix="/api/network")

class GraphResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]

def extract_emails(text: str) -> list[str]:
    if not text:
        return []
    # simple email extraction regex
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    return re.findall(email_pattern, text)

@router.get("/graph", response_model=GraphResponse)
async def get_network_graph(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email.sender, Email.recipients))
    rows = result.fetchall()
    
    nodes_set = set()
    edges_dict = {} # (sender, recipient) -> weight
    
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
                if sender_email != rec_email:
                    edge_key = (sender_email, rec_email)
                    edges_dict[edge_key] = edges_dict.get(edge_key, 0) + 1
                    
    nodes = [{"id": email, "label": email} for email in nodes_set]
    edges = [{"source": src, "target": tgt, "weight": weight} for (src, tgt), weight in edges_dict.items()]
    
    return GraphResponse(nodes=nodes, edges=edges)
