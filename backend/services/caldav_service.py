import logging
from typing import Dict, Any
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger(__name__)


def _log_safe_url(raw_url: str) -> str:
    parsed = urlsplit(raw_url)
    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, host, parsed.path, "", ""))

async def sync_caldav_accounts(session, user_id: str):
    """
    Fetch and store events locally for all CalDAV accounts of the user.
    """
    from db.models import CaldavAccount
    from sqlalchemy import select
    
    logger.info(f"Syncing CalDAV accounts for user {user_id}")
    stmt = select(CaldavAccount).where(CaldavAccount.user_id == user_id)
    result = await session.execute(stmt)
    accounts = result.scalars().all()
    
    total_parsed = 0
    for account in accounts:
        # Pseudo implementation to parse events for each account
        logger.debug(
            "Syncing CalDAV account %s at %s",
            account.id,
            _log_safe_url(account.server_url),
        )
        total_parsed += 0 # Placeholder
        
    logger.info(f"Parsed {total_parsed} events for user {user_id}")
    return True

class CalDavService:
    def __init__(self):
        pass
        
    def determine_writeback_target(self, task_context: Dict[str, Any], connected_accounts: list) -> str:
        """
        Determines the most appropriate CalDav account to write back to,
        based on the context of the task (e.g., if it originated from a company email).
        """
        # Basic ontology/context mock logic
        source_email = task_context.get("source_email", "")
        if isinstance(source_email, str) and "@" in source_email:
            source_domain = source_email.strip().lower().rsplit("@", 1)[-1]
            for account in connected_accounts:
                account_domain = str(account.get("domain", "")).lower().strip()
                if account_domain and source_domain == account_domain:
                    return account.get("account_id")
                
        # Fallback to the primary account
        if connected_accounts:
            return connected_accounts[0].get("account_id")
        return "default_system_caldav"

caldav_service = CalDavService()
