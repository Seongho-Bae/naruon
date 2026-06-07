import datetime
from typing import Optional
from icalendar import Calendar, Todo

def generate_ics_from_task(
    task_uid: str,
    title: str,
    status: str,
    created_at: datetime.datetime,
    updated_at: datetime.datetime,
    due_date: Optional[datetime.datetime] = None
) -> str:
    """
    Generates a basic CalDAV-compatible .ics (iCalendar) string for a TicketTask (VTODO).
    """
    ics_status = "NEEDS-ACTION"
    if status == "in_progress":
        ics_status = "IN-PROCESS"
    elif status == "done":
        ics_status = "COMPLETED"
    elif status == "blocked":
        ics_status = "NEEDS-ACTION"

    cal = Calendar()
    cal.add('VERSION', '2.0')
    cal.add('PRODID', '-//Naruon//AI Workspace//EN')

    todo = Todo()
    todo.add('UID', task_uid)
    todo.add('DTSTAMP', updated_at)
    todo.add('SUMMARY', title)
    todo.add('STATUS', ics_status)

    if due_date:
        todo.add('DUE', due_date)

    cal.add_component(todo)

    return cal.to_ical().decode("utf-8")
