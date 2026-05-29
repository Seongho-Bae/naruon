import asyncio
import pytest
from unittest.mock import MagicMock, patch

from db.models import TenantConfig
from services.pop3_worker import Pop3SyncWorker


def test_pop3_sync_requires_credentials(caplog, monkeypatch):
    worker = Pop3SyncWorker()
    config = TenantConfig(
        user_id="pop3-user",
        pop3_server="pop3.example.com",
        pop3_port=995,
    )
    pop3_client = MagicMock()

    monkeypatch.setattr(
        "services.pop3_worker.validate_pop3_destination",
        lambda host, port: (host, port),
    )
    with patch("services.pop3_worker.poplib.POP3_SSL", return_value=pop3_client):
        with pytest.raises(RuntimeError, match="Missing POP3 username"):
            worker._do_pop3_sync(config)

    pop3_client.user.assert_not_called()
    pop3_client.pass_.assert_not_called()
    pop3_client.quit.assert_called_once()
    assert "pop3_password" not in caplog.text
    assert "pop3-secret" not in caplog.text
    assert "credential secret" not in caplog.text.lower()


def test_pop3_sync_missing_secret_avoids_sensitive_log_names(caplog, monkeypatch):
    worker = Pop3SyncWorker()
    config = TenantConfig(
        user_id="pop3-user",
        pop3_server="pop3.example.com",
        pop3_port=995,
        pop3_username="pop3-user",
    )
    pop3_client = MagicMock()

    monkeypatch.setattr(
        "services.pop3_worker.validate_pop3_destination",
        lambda host, port: (host, port),
    )
    with patch("services.pop3_worker.poplib.POP3_SSL", return_value=pop3_client):
        with pytest.raises(RuntimeError, match="POP3 account configuration incomplete"):
            worker._do_pop3_sync(config)

    pop3_client.user.assert_not_called()
    pop3_client.pass_.assert_not_called()
    pop3_client.quit.assert_called_once()
    assert "pop3_password" not in caplog.text
    assert "password" not in caplog.text.lower()
    assert "credential secret" not in caplog.text.lower()


def test_pop3_do_sync_validates_destination_before_connect():
    worker = Pop3SyncWorker()
    config = TenantConfig(
        user_id="pop3-user",
        pop3_server="127.0.0.1",
        pop3_port=995,
    )

    with patch("services.pop3_worker.poplib.POP3_SSL") as pop3_ssl:
        with pytest.raises(ValueError):
            worker._do_pop3_sync(config)

    pop3_ssl.assert_not_called()


@pytest.mark.asyncio
async def test_pop3_worker_skips_disallowed_destination():
    worker = Pop3SyncWorker()
    config = TenantConfig(
        user_id="pop3-user",
        pop3_server="127.0.0.1",
        pop3_port=995,
    )

    with patch("services.pop3_worker.poplib.POP3_SSL") as pop3_ssl:
        await worker._sync_tenant(config, asyncio.Semaphore(1))

    pop3_ssl.assert_not_called()
