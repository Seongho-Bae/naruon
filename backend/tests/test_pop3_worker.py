import pytest
from unittest.mock import MagicMock, patch

from db.models import TenantConfig
from services.pop3_worker import Pop3SyncWorker


def test_pop3_sync_requires_credentials(caplog):
    worker = Pop3SyncWorker()
    config = TenantConfig(
        user_id="pop3-user",
        pop3_server="pop3.example.com",
        pop3_port=995,
    )
    pop3_client = MagicMock()

    with patch("services.pop3_worker.poplib.POP3_SSL", return_value=pop3_client):
        with pytest.raises(RuntimeError, match="Missing POP3 username"):
            worker._do_pop3_sync(config)

    pop3_client.user.assert_not_called()
    pop3_client.pass_.assert_not_called()
    pop3_client.quit.assert_called_once()
    assert "pop3_password" not in caplog.text
    assert "pop3-secret" not in caplog.text


def test_pop3_sync_missing_secret_avoids_sensitive_log_names(caplog):
    worker = Pop3SyncWorker()
    config = TenantConfig(
        user_id="pop3-user",
        pop3_server="pop3.example.com",
        pop3_port=995,
        pop3_username="pop3-user",
    )
    pop3_client = MagicMock()

    with patch("services.pop3_worker.poplib.POP3_SSL", return_value=pop3_client):
        with pytest.raises(RuntimeError, match="Missing POP3 credential secret"):
            worker._do_pop3_sync(config)

    pop3_client.user.assert_not_called()
    pop3_client.pass_.assert_not_called()
    pop3_client.quit.assert_called_once()
    assert "pop3_password" not in caplog.text
    assert "password" not in caplog.text.lower()
