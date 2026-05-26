import datetime
from typing import Optional


def generate_ics_from_task(
    task_uid: str,
    title: str,
    status: str,
    created_at: datetime.datetime,
    updated_at: datetime.datetime,
    due_date: Optional[datetime.datetime] = None,
) -> str:
    """
    Generates a basic CalDAV-compatible .ics (iCalendar) string for a TicketTask (VTODO).
    """
    dtstamp = updated_at.strftime("%Y%m%dT%H%M%SZ")

    # Map status
    ics_status = "NEEDS-ACTION"
    if status == "in_progress":
        ics_status = "IN-PROCESS"
    elif status == "done":
        ics_status = "COMPLETED"
    elif status == "blocked":
        ics_status = "NEEDS-ACTION"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Naruon//AI Workspace//EN",
        "BEGIN:VTODO",
        f"UID:{task_uid}",
        f"DTSTAMP:{dtstamp}",
        f"SUMMARY:{title}",
        f"STATUS:{ics_status}",
    ]

    if due_date:
        lines.append(f"DUE:{due_date.strftime('%Y%m%dT%H%M%SZ')}")

    lines.extend(["END:VTODO", "END:VCALENDAR"])

    return "\r\n".join(lines) + "\r\n"
