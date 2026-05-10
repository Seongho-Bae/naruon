import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from db import models


def test_get_fernet_fails_closed_without_encryption_key(monkeypatch):
    monkeypatch.setattr(models.settings, "ENCRYPTION_KEY", None, raising=False)

    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        models.get_fernet()


def test_get_fernet_fails_closed_with_blank_encryption_key(monkeypatch):
    monkeypatch.setattr(models.settings, "ENCRYPTION_KEY", SecretStr(""), raising=False)

    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        models.get_fernet()


def test_get_fernet_accepts_configured_encryption_key(monkeypatch):
    configured_key = Fernet.generate_key().decode()
    monkeypatch.setattr(
        models.settings,
        "ENCRYPTION_KEY",
        SecretStr(configured_key),
        raising=False,
    )

    fernet = models.get_fernet()
    token = fernet.encrypt(b"secret")

    assert fernet.decrypt(token) == b"secret"
