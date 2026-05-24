import hashlib
import logging
from typing import Dict, Any
import email.utils

logger = logging.getLogger(__name__)

def generate_email_fingerprint(email_data: Dict[str, Any]) -> str:
    """
    Generates a unique fingerprint for an email based on its sender, subject, date, and body content.
    Used to de-duplicate emails from ZIP imports or forwarding loops.
    """
    sender = str(email_data.get("sender") or "")
    subject = str(email_data.get("subject") or "")
    date = str(email_data.get("date") or "")
    body = str(email_data.get("body") or "")
    body_snippet = body[:500] # First 500 chars
    
    raw_str = f"{sender}|{subject}|{date}|{body_snippet}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def detect_reply_tracking(email_data: Dict[str, Any]) -> bool:
    """
    Detects if the user sent an email that expects a reply.
    """
    body = str(email_data.get("body") or "").lower()
    return "please reply" in body or "?" in body

def process_self_to_self(email_data: Dict[str, Any], user_email: str) -> bool:
    """
    Detects if an email is sent from the user to themselves, turning it into a knowledge node.
    """
    sender_raw = str(email_data.get("sender") or "")
    recipients_raw = str(email_data.get("recipients") or "")
    
    _, sender_addr = email.utils.parseaddr(sender_raw)
    parsed_recipients = [addr for _, addr in email.utils.getaddresses([recipients_raw])]
    
    if user_email == sender_addr and user_email in parsed_recipients:
        logger.info("Self-to-self email detected. Organizing as knowledge node.")
        return True
    return False
