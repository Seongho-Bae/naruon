from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import AuthContext, get_auth_context
from services.calendar_service import create_calendar_event
from services.exceptions import CalendarServiceError

router = APIRouter(prefix="/api/calendar")


class SyncRequest(BaseModel):
    todos: list[str]
    user_token: dict | None = None


def get_calendar_credentials_for_user(auth_context: AuthContext) -> dict | None:
    """Return server-side calendar credentials for the authenticated user.

    Body-provided tokens are intentionally ignored. A future calendar account
    aggregate should load encrypted OAuth credentials here; until then the route
    fails closed instead of turning the caller identity into Google credentials.
    """

    return None


@router.post("/sync")
async def sync_todos(
    request: SyncRequest, auth_context: AuthContext = Depends(get_auth_context)
):
    try:
        results = []
        calendar_credentials = get_calendar_credentials_for_user(auth_context)
        if not calendar_credentials:
            raise HTTPException(
                status_code=503,
                detail="Calendar credentials are not configured for this user",
            )
        for todo in request.todos:
            event = await create_calendar_event(todo, calendar_credentials)
            results.append(event)
        return {"synced": len(results), "events": results}
    except CalendarServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
