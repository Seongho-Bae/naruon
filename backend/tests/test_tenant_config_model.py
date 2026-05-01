from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from db import models
from db.models import TenantConfig


TEST_ENCRYPTION_KEY = SecretStr(Fernet.generate_key().decode("ascii"))


@pytest.fixture(autouse=True)
def configured_test_encryption_key(monkeypatch):
    monkeypatch.setattr(models.settings, "ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TenantConfig.__table__.create(engine)
    with Session(engine) as session:
        yield session


def test_tenant_config_model_exists():
    config = TenantConfig(user_id="test_user", openai_api_key="test_key")
    assert config.user_id == "test_user"
    assert config.openai_api_key == "test_key"


def test_tenant_config_model_encryption(db_session):
    config = TenantConfig(user_id="test_user2", openai_api_key="test_key2")
    db_session.add(config)
    db_session.commit()

    # Query back to ensure it can be decrypted properly
    saved_config = (
        db_session.query(TenantConfig).filter_by(user_id="test_user2").first()
    )
    assert saved_config.openai_api_key == "test_key2"

    # Verify that the value in the database is actually encrypted
    result = db_session.execute(
        text("SELECT openai_api_key FROM tenant_configs WHERE user_id='test_user2'")
    ).scalar()
    assert result != "test_key2"
    assert result is not None
    assert isinstance(result, str)

    # Verify __repr__ does not expose sensitive keys
    repr_str = repr(saved_config)
    assert "test_key2" not in repr_str
    assert "has_openai_key=True" in repr_str


def test_encrypted_string_fails_closed_without_encryption_key(monkeypatch):
    monkeypatch.setattr(models.settings, "ENCRYPTION_KEY", None)

    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        models.get_fernet()


def test_models_do_not_define_a_hardcoded_fallback_key():
    source = Path(__file__).resolve().parents[1] / "db" / "models.py"

    assert "FALLBACK_KEY" not in source.read_text()
