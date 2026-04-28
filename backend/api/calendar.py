from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.calendar_service import create_calendar_event
from services.exceptions import CalendarServiceError

router = APIRouter(prefix="/api/calendar")


class SyncRequest(BaseModel):
    todos: list[str]
    user_token: dict


@router.post("/sync")
async def sync_todos(request: SyncRequest):
    try:
        results = []
        for todo in request.todos:
            event = await create_calendar_event(todo, request.user_token)
            results.append(event)
        return {"synced": len(results), "events": results}
    except CalendarServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
