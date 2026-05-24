import pytest
from services.caldav_service import caldav_service

def test_determine_writeback_target():
    connected_accounts = [
        {"account_id": "account1", "domain": "company.com"},
        {"account_id": "account2", "domain": "personal.com"}
    ]
    
    # Should match company.com
    task_context_1 = {"source_email": "boss@company.com"}
    target_1 = caldav_service.determine_writeback_target(task_context_1, connected_accounts)
    assert target_1 == "account1"
    
    # Should fallback to primary
    task_context_2 = {"source_email": "friend@other.com"}
    target_2 = caldav_service.determine_writeback_target(task_context_2, connected_accounts)
    assert target_2 == "account1"
