import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

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
            source_domain = source_email.split("@")[1].lower().strip()
            for account in connected_accounts:
                account_domain = str(account.get("domain", "")).lower().strip()
                if account_domain and source_domain == account_domain:
                    return account.get("account_id")
                
        # Fallback to the primary account
        if connected_accounts:
            return connected_accounts[0].get("account_id")
        return "default_system_caldav"

caldav_service = CalDavService()
