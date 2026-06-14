import pytest
from services.caldav_service import caldav_service

def test_determine_writeback_target():
    connected_accounts = [
        {
            "source_id": "caldav_src_company",
            "domain": "company.com",
            "writeback_enabled": True,
        },
        {
            "source_id": "caldav_src_personal",
            "domain": "personal.com",
            "writeback_enabled": True,
        },
    ]
    
    # Should match company.com
    task_context_1 = {"source_email": "boss@company.com"}
    target_1 = caldav_service.determine_writeback_target(task_context_1, connected_accounts)
    assert target_1 == "caldav_src_company"
    
    # Should fallback to primary
    task_context_2 = {"source_email": "friend@other.com"}
    target_2 = caldav_service.determine_writeback_target(task_context_2, connected_accounts)
    assert target_2 == "caldav_src_company"

    # Should not match substring domain collisions
    task_context_3 = {"source_email": "attacker@evilcompany.com"}
    target_3 = caldav_service.determine_writeback_target(task_context_3, connected_accounts)
    assert target_3 == "caldav_src_company"  # fallback, not domain match

def test_determine_writeback_target_no_accounts():
    task_context = {"source_email": "boss@company.com"}
    target = caldav_service.determine_writeback_target(task_context, [])
    assert target is None


def test_determine_writeback_target_ignores_internal_account_ids():
    task_context = {"source_email": "boss@company.com"}
    connected_accounts = [
        {
            "account_id": "account1",
            "domain": "company.com",
            "writeback_enabled": True,
        },
    ]

    target = caldav_service.determine_writeback_target(task_context, connected_accounts)

    assert target is None


def test_determine_writeback_target_requires_writeback_eligibility():
    task_context = {"source_email": "boss@company.com"}
    connected_accounts = [
        {
            "source_id": "caldav_src_company",
            "domain": "company.com",
            "writeback_enabled": False,
        },
    ]

    target = caldav_service.determine_writeback_target(task_context, connected_accounts)

    assert target is None
