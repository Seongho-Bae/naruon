import pytest

from runner.local_mail_adapters import LocalMailAccountConfig, LocalMailAdapters


@pytest.mark.asyncio
async def test_local_smtp_adapter_sends_through_configured_provider(monkeypatch):
    sent = []

    async def fake_send_email(message_params, smtp_config):
        sent.append((message_params, smtp_config))
        return {"status": "sent", "simulated": False}

    monkeypatch.setattr("runner.local_mail_adapters.send_email", fake_send_email)
    adapters = LocalMailAdapters(
        [
            LocalMailAccountConfig(
                account="mailbox-1",
                user_id="user-1",
                organization_id="org-1",
                smtp_server="smtp.example.com",
                smtp_port=587,
                smtp_username="sender@example.com",
                smtp_password="smtp-secret",
            )
        ]
    )

    result = await adapters.send_smtp(
        {
            "account": "mailbox-1",
            "to": "recipient@example.com",
            "subject": "Runner send",
            "body": "Sent by the local connector.",
            "in_reply_to": "<parent@example.com>",
            "references": "<parent@example.com>",
        }
    )

    assert result == {
        "status": "success",
        "provider_write_executed": True,
        "provider_status": "sent",
    }
    message_params, smtp_config = sent[0]
    assert message_params.to_address == "recipient@example.com"
    assert message_params.subject == "Runner send"
    assert message_params.body == "Sent by the local connector."
    assert message_params.in_reply_to == "<parent@example.com>"
    assert message_params.references == "<parent@example.com>"
    assert smtp_config.smtp_server == "smtp.example.com"
    assert smtp_config.smtp_port == 587
    assert smtp_config.smtp_username == "sender@example.com"
    assert smtp_config.smtp_password == "smtp-secret"


@pytest.mark.asyncio
async def test_local_smtp_adapter_fails_closed_when_account_config_is_incomplete():
    adapters = LocalMailAdapters(
        [
            LocalMailAccountConfig(
                account="mailbox-1",
                user_id="user-1",
                organization_id="org-1",
                smtp_username="sender@example.com",
            )
        ]
    )

    result = await adapters.send_smtp(
        {
            "account": "mailbox-1",
            "to": "recipient@example.com",
            "subject": "Runner send",
            "body": "body",
        }
    )

    assert result == {
        "status": "error",
        "error": "account_configuration_incomplete",
        "error_code": "account_configuration_incomplete",
        "provider_write_executed": False,
    }


@pytest.mark.asyncio
async def test_local_imap_adapter_imports_with_configured_worker():
    synced_configs = []

    class FakeImapWorker:
        async def _sync_tenant(self, config):
            synced_configs.append(config)
            return 3

    adapters = LocalMailAdapters(
        [
            LocalMailAccountConfig(
                account="mailbox-1",
                user_id="user-1",
                organization_id="org-1",
                imap_server="imap.example.com",
                imap_port=993,
                imap_username="reader@example.com",
                imap_password="imap-secret",
            )
        ],
        imap_worker_factory=FakeImapWorker,
    )

    result = await adapters.fetch_imap({"account": "mailbox-1"})

    assert result == {
        "status": "success",
        "messages_imported": 3,
        "provider_write_executed": False,
    }
    assert len(synced_configs) == 1
    synced_config = synced_configs[0]
    assert synced_config.user_id == "user-1"
    assert synced_config.organization_id == "org-1"
    assert synced_config.imap_server == "imap.example.com"
    assert synced_config.imap_port == 993
    assert synced_config.imap_username == "reader@example.com"
    assert synced_config.imap_password == "imap-secret"
