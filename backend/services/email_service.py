import hashlib
import logging
import unicodedata
from typing import Dict, Any
from email.utils import parseaddr, getaddresses

logger = logging.getLogger(__name__)


def _canonical_email_identity(value: str) -> str | None:
    normalized_value = unicodedata.normalize("NFKC", str(value or "")).strip()
    _, parsed_address = parseaddr(normalized_value)
    address = parsed_address or normalized_value
    address = unicodedata.normalize("NFKC", address).strip().casefold()
    if "@" not in address:
        return None
    local_part, _, domain_part = address.partition("@")
    local_part = local_part.partition("+")[0].strip()
    domain_part = domain_part.strip()
    if not local_part or not domain_part:
        return None
    try:
        domain_part = domain_part.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    return f"{local_part}@{domain_part}"


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


def process_self_to_self(email_data: Dict[str, Any], user_email: str) -> bool:
    """
    Detects if an email is sent from the user to themselves, turning it into a knowledge node.
    """
    sender_raw = str(email_data.get("sender") or "")
    recipients_raw = email_data.get("recipients") or []
    recipient_inputs = recipients_raw if isinstance(recipients_raw, list) else [recipients_raw]
    recipient_inputs = [str(v) for v in recipient_inputs]

    _, sender_addr = parseaddr(sender_raw)
    normalized_user = _canonical_email_identity(user_email)
    normalized_sender = _canonical_email_identity(sender_addr or sender_raw)
    parsed_recipients: set[str] = set()
    for recipient_input in recipient_inputs:
        parsed_addresses = [addr for _, addr in getaddresses([recipient_input])]
        if not parsed_addresses:
            parsed_addresses = [recipient_input]
        for addr in parsed_addresses:
            normalized = _canonical_email_identity(addr)
            if normalized is not None:
                parsed_recipients.add(normalized)

    if (
        normalized_user
        and normalized_user == normalized_sender
        and normalized_user in parsed_recipients
    ):
        logger.info("Self-to-self email detected. Organizing as knowledge node.")
        return True
    return False
