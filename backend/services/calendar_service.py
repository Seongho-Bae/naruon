import asyncio
import datetime
import unicodedata

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .exceptions import CalendarServiceError, UnsafeCalendarTodoError

MAX_CALENDAR_TODO_LENGTH = 500
UNSAFE_CALENDAR_TODO_SEQUENCES = ("<", ">", "`", "$(", "${")


def validate_calendar_todo_text(todo_text: str) -> str:
    """Validate user-authored calendar text before external writeback."""
    normalized = todo_text.strip()
    if not normalized or len(normalized) > MAX_CALENDAR_TODO_LENGTH:
        raise UnsafeCalendarTodoError("Unsafe calendar todo text")
    if any(unicodedata.category(character) == "Cc" for character in normalized):
        raise UnsafeCalendarTodoError("Unsafe calendar todo text")
    if any(sequence in normalized for sequence in UNSAFE_CALENDAR_TODO_SEQUENCES):
        raise UnsafeCalendarTodoError("Unsafe calendar todo text")
    return normalized


async def create_calendar_event(todo_text: str, user_token: dict) -> dict:
    """Creates a calendar event for a given TODO text."""
    try:
        safe_todo_text = validate_calendar_todo_text(todo_text)
        creds = Credentials(**user_token)
        service = build("calendar", "v3", credentials=creds)

        now = datetime.datetime.now(datetime.timezone.utc)
        event = {
            "summary": safe_todo_text,
            "start": {"dateTime": now.isoformat()},
            "end": {"dateTime": (now + datetime.timedelta(hours=1)).isoformat()},
        }
        request = service.events().insert(calendarId="primary", body=event)
        created_event = await asyncio.to_thread(request.execute)
        return created_event
    except UnsafeCalendarTodoError:
        raise
    except Exception as e:
        raise CalendarServiceError(f"Failed to create event: {str(e)}") from e
