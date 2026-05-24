import hashlib
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def generate_email_fingerprint(email_data: Dict[str, Any]) -> str:
    """
    Generates a unique fingerprint for an email based on its sender, subject, date, and body content.
    Used to de-duplicate emails from ZIP imports or forwarding loops.
    """
    sender = email_data.get("sender", "")
    subject = email_data.get("subject", "")
    date = str(email_data.get("date", ""))
    body_snippet = email_data.get("body", "")[:500] # First 500 chars
    
    raw_str = f"{sender}|{subject}|{date}|{body_snippet}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def detect_reply_tracking(email_data: Dict[str, Any]) -> bool:
    """
    Detects if the user sent an email that expects a reply.
    """
    body = email_data.get("body", "").lower()
    return "please reply" in body or "?" in body

def process_self_to_self(email_data: Dict[str, Any], user_email: str) -> bool:
    """
    Detects if an email is sent from the user to themselves, turning it into a knowledge node.
    """
    sender = email_data.get("sender", "")
    recipients = email_data.get("recipients", "")
    
    if user_email in sender and user_email in recipients:
        logger.info(f"Self-to-self email detected. Organizing as knowledge node.")
        return True
    return False
