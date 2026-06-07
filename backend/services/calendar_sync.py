import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class CalendarTask:
    task_uid: str
    title: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    due_date: Optional[datetime.datetime] = None


def generate_ics_from_task(task: CalendarTask) -> str:
    """
    Generates a basic CalDAV-compatible .ics (iCalendar) string for a TicketTask (VTODO).
    """
    dtstamp = task.updated_at.strftime("%Y%m%dT%H%M%SZ")

    # Map status
    ics_status = "NEEDS-ACTION"
    if task.status == "in_progress":
        ics_status = "IN-PROCESS"
    elif task.status == "done":
        ics_status = "COMPLETED"
    elif task.status == "blocked":
        ics_status = "NEEDS-ACTION"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Naruon//AI Workspace//EN",
        "BEGIN:VTODO",
        f"UID:{task.task_uid}",
        f"DTSTAMP:{dtstamp}",
        f"SUMMARY:{task.title}",
        f"STATUS:{ics_status}",
    ]

    if task.due_date:
        lines.append(f"DUE:{task.due_date.strftime('%Y%m%dT%H%M%SZ')}")

    lines.extend(["END:VTODO", "END:VCALENDAR"])

    return "\r\n".join(lines) + "\r\n"
