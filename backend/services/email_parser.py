import email
from html.parser import HTMLParser
from email import policy
from pathlib import Path
import datetime
from email.utils import parsedate_to_datetime
from typing import TypedDict
from .exceptions import EmailParseError


class EmailData(TypedDict):
    """Parsed email data structure."""

    message_id: str
    thread_id: str | None
    sender: str
    reply_to: str | None
    recipients: str
    subject: str
    in_reply_to: str | None
    references: str | None
    date: datetime.datetime
    body: str
    attachments: list[dict]


def _sanitize_nul(text: str) -> str:
    """Removes NUL characters from strings before PostgreSQL text storage."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return text.replace("\x00", "")


class _HTMLBodyTextExtractor(HTMLParser):
    """Extracts display text from untrusted email HTML without executable markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip_depth += 1
            return
        if tag.lower() in {"br", "div", "li", "p", "tr"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag.lower() in {"div", "li", "p", "tr"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def sanitize_email_html_to_text(html_body: str) -> str:
    """Converts untrusted email HTML into non-executable display text."""
    parser = _HTMLBodyTextExtractor()
    parser.feed(html_body)
    parser.close()
    lines = [line.strip() for line in parser.text().splitlines()]
    return "\n".join(line for line in lines if line)


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

    body = plain_body if plain_body else sanitize_email_html_to_text(html_body)

    date_header = msg.get("Date")
    parsed_date = None
    if date_header:
        try:
            parsed_date = parsedate_to_datetime(date_header)
        except (TypeError, ValueError):
            parsed_date = None

    if not parsed_date:
        parsed_date = datetime.datetime.now(datetime.timezone.utc)

    message_id = _sanitize_nul(msg.get("Message-ID", ""))

    # Extract thread_id
    thread_id = None
    references = msg.get("References")  # O3: email threading support
    in_reply_to = msg.get("In-Reply-To")

    if references:
        # Get the first reference as the root thread ID
        refs = references.split()
        if refs:
            thread_id = _sanitize_nul(refs[0])

    if not thread_id and in_reply_to:
        in_reply_to_list = in_reply_to.split()
        if in_reply_to_list:
            thread_id = _sanitize_nul(in_reply_to_list[0])

    if not thread_id:
        thread_id = message_id

    return {
        "message_id": message_id,
        "thread_id": thread_id,
        "sender": _sanitize_nul(msg.get("From", "")),
        "reply_to": _sanitize_nul(msg.get("Reply-To", ""))
        if msg.get("Reply-To")
        else None,
        "recipients": _sanitize_nul(msg.get("To", "")),
        "subject": _sanitize_nul(msg.get("Subject", "")),
        "in_reply_to": _sanitize_nul(msg.get("In-Reply-To", ""))
        if msg.get("In-Reply-To")
        else None,
        "references": _sanitize_nul(msg.get("References", ""))
        if msg.get("References")
        else None,
        "date": parsed_date,
        "body": _sanitize_nul(body),
        "attachments": attachments,
    }
