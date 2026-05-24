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
        for account in connected_accounts:
            if account.get("domain") in source_email:
                return account.get("account_id")
                
        # Fallback to the primary account
        if connected_accounts:
            return connected_accounts[0].get("account_id")
        return "default_system_caldav"

caldav_service = CalDavService()
