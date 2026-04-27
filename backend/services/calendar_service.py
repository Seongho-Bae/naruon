from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
from core.config import settings
from .exceptions import CalendarServiceError

async def create_calendar_event(todo_text: str, user_token: dict) -> dict:
    """Creates a calendar event for a given TODO text."""
    try:
        creds = Credentials(**user_token)
        service = build("calendar", "v3", credentials=creds)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        event = {
            "summary": todo_text,
            "start": {"dateTime": now.isoformat()},
            "end": {"dateTime": (now + datetime.timedelta(hours=1)).isoformat()}
        }
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        return created_event
    except Exception as e:
        raise CalendarServiceError(f"Failed to create event: {str(e)}")
