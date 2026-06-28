import hashlib
import logging
import unicodedata
from typing import Dict, Any
from email.utils import parseaddr, getaddresses

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

    raw_str = f"{sender}|{subject}|{date}|{body}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def _normalize_email_address(addr: str) -> str:
    """Normalize an email address using NFKC Unicode normalization and lowercasing (CWE-178)."""
    return unicodedata.normalize("NFKC", addr).strip().lower()


def process_self_to_self(email_data: Dict[str, Any], user_email: str) -> bool:
    """
    Detects if an email is sent from the user to themselves, turning it into a knowledge node.
    """
    sender_raw = str(email_data.get("sender") or "")
    recipients_raw = email_data.get("recipients") or []
    recipient_inputs = recipients_raw if isinstance(recipients_raw, list) else [recipients_raw]
    recipient_inputs = [str(v) for v in recipient_inputs]

    _, sender_addr = parseaddr(sender_raw)
    normalized_user = _normalize_email_address(user_email)
    normalized_sender = _normalize_email_address(sender_addr)
    parsed_recipients = {
        _normalize_email_address(addr)
        for _, addr in getaddresses(recipient_inputs)
        if addr
    }

    if normalized_user and normalized_user == normalized_sender and normalized_user in parsed_recipients:
        logger.info("Self-to-self email detected. Organizing as knowledge node.")
        return True
    return False
