from __future__ import annotations

import re

from collections.abc import Sequence

from db.models import MailboxAccount


def _extract_mailboxes(value: str | None) -> set[str]:
    if not value:
        return set()
    mailboxes = set()
    for token in re.split(r"[,;]", value):
        match = re.search(r"<([^>]+)>", token)
        mailbox = (match.group(1) if match else token).strip().lower()
        if mailbox:
            mailboxes.add(mailbox)
    return mailboxes


def _account_mailboxes(account: MailboxAccount) -> set[str]:
    return {
        mailbox.lower()
        for mailbox in [
            account.email_address,
            account.smtp_username,
            account.imap_username,
        ]
        if mailbox
    }


def resolve_mailbox_account_id_for_email(
    accounts: Sequence[MailboxAccount],
    *,
    sender: str | None,
    reply_to: str | None,
    recipients: str | None,
) -> int | None:
    active_accounts = [
        account for account in accounts if getattr(account, "is_active", True)
    ]
    if not active_accounts:
        return None

    email_mailboxes = set()
    email_mailboxes |= _extract_mailboxes(sender)
    email_mailboxes |= _extract_mailboxes(reply_to)
    email_mailboxes |= _extract_mailboxes(recipients)

    matches = [
        account
        for account in active_accounts
        if not _account_mailboxes(account).isdisjoint(email_mailboxes)
    ]
    if matches:
        default_match = next(
            (account for account in matches if account.is_default_reply), None
        )
        return (default_match or matches[0]).id

    if len(active_accounts) == 1:
        return active_accounts[0].id

    default_account = next(
        (account for account in active_accounts if account.is_default_reply), None
    )
    return default_account.id if default_account else None
