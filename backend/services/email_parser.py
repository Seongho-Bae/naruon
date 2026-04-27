import email
from email import policy
from pathlib import Path
import datetime
from email.utils import parsedate_to_datetime

def parse_eml(file_path: str | Path) -> dict:
    with open(file_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
        
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and not part.get_filename():
                body = part.get_content()
                break
    else:
        body = msg.get_content()
        
    date_header = msg.get("Date")
    parsed_date = parsedate_to_datetime(date_header) if date_header else datetime.datetime.now(datetime.timezone.utc)
        
    return {
        "message_id": msg.get("Message-ID", ""),
        "sender": msg.get("From", ""),
        "recipients": msg.get("To", ""),
        "subject": msg.get("Subject", ""),
        "date": parsed_date,
        "body": body
    }
