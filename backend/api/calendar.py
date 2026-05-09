from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import get_current_user
from services.calendar_service import create_calendar_event
from services.exceptions import CalendarServiceError

router = APIRouter(prefix="/api/calendar")


class SyncRequest(BaseModel):
    todos: list[str]
    user_token: dict


@router.post("/sync")
async def sync_todos(
    request: SyncRequest,
    _current_user: str = Depends(get_current_user),
):
    try:
        results = []
        for todo in request.todos:
            event = await create_calendar_event(todo, request.user_token)
            results.append(event)
        return {"synced": len(results), "events": results}
    except CalendarServiceError:
        raise HTTPException(status_code=500, detail="Calendar sync failed")
