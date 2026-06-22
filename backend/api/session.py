from fastapi import APIRouter, Depends
from pydantic import BaseModel

import jwt
from fastapi import HTTPException
from core.config import settings
from api.auth import jwks_client, issue_signed_session_token, OIDC_ALLOWED_ALGORITHMS
from api.auth import AuthContext, get_auth_context


router = APIRouter(prefix="/api/auth", tags=["auth"])


class SessionResponse(BaseModel):
    user_id: str
    organization_id: str | None
    workspace_id: str


@router.get("/session", response_model=SessionResponse, dependencies=[Depends(get_auth_context)])
async def current_session(
    auth_context: AuthContext = Depends(get_auth_context),
) -> SessionResponse:
    return SessionResponse(
        user_id=auth_context.user_id,
        organization_id=auth_context.organization_id,
        workspace_id=auth_context.workspace_id,
    )

class OIDCExchangeRequest(BaseModel):
    id_token: str

class OIDCExchangeResponse(BaseModel):
    naruon_session: str

@router.post("/session/oidc-exchange", response_model=OIDCExchangeResponse)
async def oidc_exchange(request: OIDCExchangeRequest) -> OIDCExchangeResponse:
    if not settings.OIDC_ISSUER_URL:
        raise HTTPException(status_code=503, detail="OIDC is not configured")

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(request.id_token) if jwks_client else None
        payload = jwt.decode(
            request.id_token,
            signing_key.key if signing_key else '',
            algorithms=OIDC_ALLOWED_ALGORITHMS,
            audience=settings.OIDC_CLIENT_ID,
            issuer=settings.OIDC_ISSUER_URL,
            options={
                "require": ["exp", "iss", "aud", "sub"],
                "verify_signature": True,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    # Extract required claims
    sub = payload.get("sub")
    role = payload.get("role")
    workspace = payload.get("workspace")
    if not isinstance(sub, str) or not isinstance(role, str) or not isinstance(workspace, str):
         raise HTTPException(status_code=401, detail="Invalid token claims")

    # Ensure role is not admin as browser-side OIDC support does not mint local roles
    # The requirement is that we extract "organization_id" which is `org`
    org = payload.get("org")

    # Issue an HMAC signed session
    # We must satisfy the backend's signed claim contract:
    # sub, role, org, groups, workspace
    session_payload = {
        "sub": sub,
        "role": role,
        "org": org,
        "groups": payload.get("groups", []),
        "workspace": workspace,
    }

    token = issue_signed_session_token(session_payload)
    response = OIDCExchangeResponse(naruon_session=token)
    return response
