from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/runtime-config", tags=["runtime-config"])

class RuntimeConfigResponse(BaseModel):
    product_name: str
    version: str
    features: dict[str, bool]

@router.get("", response_model=RuntimeConfigResponse)
async def get_runtime_config():
    # Return basic non-secret configuration
    return RuntimeConfigResponse(
        product_name="Naruon",
        version="0.5.1",
        features={
            "llm_enabled": True,
            "smtp_enabled": True,
            "imap_enabled": True
        }
    )
