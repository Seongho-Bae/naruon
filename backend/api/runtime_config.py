from fastapi import APIRouter
from pydantic import BaseModel

from core.config import settings

router = APIRouter(prefix="/api/runtime-config", tags=["runtime-config"])


class RuntimeConfigResponse(BaseModel):
    product_name: str
    version: str
    features: dict[str, bool]


@router.get("", response_model=RuntimeConfigResponse)
async def get_runtime_config():
    # Return basic non-secret configuration
    manual_bearer_login_enabled = (
        settings.AUTH_MODE in {"hybrid", "oidc"}
        and bool(settings.OIDC_ISSUER)
        and bool(settings.OIDC_AUDIENCE)
        and bool(settings.OIDC_SHARED_SECRET or settings.OIDC_JWKS_URL)
    )
    return RuntimeConfigResponse(
        product_name="Naruon",
        version="0.5.1",
        features={
            "llm_enabled": True,
            "smtp_enabled": True,
            "imap_enabled": True,
            "dev_header_auth_enabled": False,
            "manual_bearer_login_enabled": manual_bearer_login_enabled,
        },
    )
