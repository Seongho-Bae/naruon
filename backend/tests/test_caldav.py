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

    # Should not match substring domain collisions
    task_context_3 = {"source_email": "attacker@evilcompany.com"}
    target_3 = caldav_service.determine_writeback_target(task_context_3, connected_accounts)
    assert target_3 == "account1"  # fallback, not domain match

def test_determine_writeback_target_no_accounts():
    task_context = {"source_email": "boss@company.com"}
    target = caldav_service.determine_writeback_target(task_context, [])
    assert target == "default_system_caldav"
