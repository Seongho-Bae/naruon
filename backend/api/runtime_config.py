from fastapi import APIRouter
from pydantic import BaseModel

from core.version import get_release_version

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
        version=get_release_version(),
        features={
            "llm_enabled": True,
            "smtp_enabled": True,
            "imap_enabled": True,
        },
    )
