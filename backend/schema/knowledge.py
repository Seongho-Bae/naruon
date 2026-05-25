from pydantic import BaseModel, Field
from typing import List, Optional

class KnowledgeNode(BaseModel):
    title: str = Field(..., description="The title of the extracted knowledge.")
    content: str = Field(..., description="The core content or summary of the knowledge.")
    tags: List[str] = Field(default_factory=list, description="Tags associated with this knowledge.")
    source_email_id: Optional[int] = None
