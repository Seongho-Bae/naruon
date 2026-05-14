from db.models import MailboxAccount
from services.mailbox_routing import resolve_mailbox_account_id_for_email


def test_resolve_mailbox_account_matches_recipient_mailbox():
    accounts = [
        MailboxAccount(
            id=1,
            user_id="testuser",
            email_address="alpha@example.com",
            display_name="Alpha",
            provider="custom",
            is_default_reply=False,
            is_active=True,
        ),
        MailboxAccount(
            id=2,
            user_id="testuser",
            email_address="beta@example.com",
            display_name="Beta",
            provider="custom",
            is_default_reply=True,
            is_active=True,
        ),
    ]

    resolved = resolve_mailbox_account_id_for_email(
        accounts,
        sender="outside@example.com",
        reply_to=None,
        recipients="beta@example.com",
    )

    assert resolved == 2


def test_resolve_mailbox_account_matches_sender_for_sent_mail():
    accounts = [
        MailboxAccount(
            id=3,
            user_id="testuser",
            email_address="owner@example.com",
            display_name="Owner",
            provider="custom",
            is_default_reply=True,
            is_active=True,
        )
    ]

    resolved = resolve_mailbox_account_id_for_email(
        accounts,
        sender="owner@example.com",
        reply_to=None,
        recipients="partner@example.com",
    )

    assert resolved == 3


def test_resolve_mailbox_account_falls_back_to_single_active_account_when_no_header_match():
    accounts = [
        MailboxAccount(
            id=4,
            user_id="testuser",
            email_address="solo@example.com",
            display_name="Solo",
            provider="custom",
            is_default_reply=False,
            is_active=True,
        )
    ]

    resolved = resolve_mailbox_account_id_for_email(
        accounts,
        sender="outside@example.com",
        reply_to=None,
        recipients="unknown@example.com",
    )

    assert resolved == 4
