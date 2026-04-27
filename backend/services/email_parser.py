import email
from email import policy
from pathlib import Path
import datetime
from email.utils import parsedate_to_datetime
from typing import TypedDict
from .exceptions import EmailParseError


class EmailData(TypedDict):
    """Parsed email data structure."""

    message_id: str
    sender: str
    recipients: str
    subject: str
    date: datetime.datetime
    body: str
    attachments: list[dict]


def _sanitize_nul(text: str) -> str:
    """Removes NUL characters from strings, which are invalid in PostgreSQL text fields."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return text.replace("\x00", "")


def parse_eml(file_path: str | Path) -> EmailData:
    """Parses an EML file and extracts email metadata and body.

    Raises:
        EmailParseError: If there is an issue reading the file.
    """
    try:
        with open(file_path, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
    except OSError as e:
        raise EmailParseError(f"Failed to read file {file_path}: {e}") from e

    plain_body = ""
    html_body = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            filename = part.get_filename()
            # Skip attachments
            if filename:
                if content_type == "text/plain":
                    part_content = part.get_content()
                    if isinstance(part_content, str):
                        attachments.append(
                            {
                                "filename": _sanitize_nul(filename),
                                "content": _sanitize_nul(part_content),
                            }
                        )
                continue

            if content_type == "text/plain":
                part_content = part.get_content()
                if isinstance(part_content, str):
                    plain_body += part_content
            elif content_type == "text/html":
                part_content = part.get_content()
                if isinstance(part_content, str):
                    html_body += part_content
    else:
        content_type = msg.get_content_type()
        part_content = msg.get_content()
        if isinstance(part_content, str):
            if content_type == "text/html":
                html_body = part_content
            else:
                plain_body = part_content

    body = plain_body if plain_body else html_body

    date_header = msg.get("Date")
    parsed_date = None
    if date_header:
        try:
            parsed_date = parsedate_to_datetime(date_header)
        except (TypeError, ValueError):
            parsed_date = None

    if not parsed_date:
        parsed_date = datetime.datetime.now(datetime.timezone.utc)

    return {
        "message_id": _sanitize_nul(msg.get("Message-ID", "")),
        "sender": _sanitize_nul(msg.get("From", "")),
        "recipients": _sanitize_nul(msg.get("To", "")),
        "subject": _sanitize_nul(msg.get("Subject", "")),
        "date": parsed_date,
        "body": _sanitize_nul(body),
        "attachments": attachments,
    }
