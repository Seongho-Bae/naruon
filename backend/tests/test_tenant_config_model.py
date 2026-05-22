import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from db.models import EncryptedString, TenantConfig, get_fernet
from core.config import settings

TEST_OPENAI_KEY = "test_key2"  # noqa: S105
TEST_IMAP_PASSWORD = "imap-secret"  # noqa: S105
TEST_SMTP_PASSWORD = "smtp-secret"  # noqa: S105
WEAK_FERNET_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


@pytest.fixture(autouse=True)
def mock_debug():
    old_debug = settings.DEBUG
    old_encryption_key = settings.ENCRYPTION_KEY
    settings.DEBUG = True
    settings.ENCRYPTION_KEY = SecretStr(Fernet.generate_key().decode("ascii"))
    yield
    settings.DEBUG = old_debug
    settings.ENCRYPTION_KEY = old_encryption_key


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


def test_get_fernet_requires_encryption_key_even_when_debug_enabled():
    settings.ENCRYPTION_KEY = None

    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY is required"):
        get_fernet()


def test_get_fernet_rejects_non_fernet_key_without_derivation():
    settings.ENCRYPTION_KEY = SecretStr("test-encryption-key")

    with pytest.raises(RuntimeError, match="valid Fernet key"):
        get_fernet()


def test_get_fernet_rejects_low_entropy_fernet_key():
    settings.ENCRYPTION_KEY = SecretStr(WEAK_FERNET_KEY)

    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        get_fernet()


def test_encrypted_string_returns_none_on_tampered_ciphertext():
    encrypted_string = EncryptedString()
    encrypted_value = encrypted_string.process_bind_param(TEST_SMTP_PASSWORD, None)
    assert encrypted_value is not None
    tampered_value = encrypted_value[:-1] + ("A" if encrypted_value[-1] != "A" else "B")

    decrypted_value = encrypted_string.process_result_value(tampered_value, None)

    assert decrypted_value is None
    assert decrypted_value != tampered_value


def test_encrypted_string_returns_none_on_wrong_key_without_leaking_ciphertext():
    encrypted_string = EncryptedString()
    encrypted_value = encrypted_string.process_bind_param(TEST_IMAP_PASSWORD, None)
    assert encrypted_value is not None
    settings.ENCRYPTION_KEY = SecretStr(Fernet.generate_key().decode("ascii"))

    decrypted_value = encrypted_string.process_result_value(encrypted_value, None)

    assert decrypted_value is None
    assert decrypted_value != encrypted_value


def test_tenant_config_model_encryption(db_session):
    config = TenantConfig(
        user_id="test_user2",
        openai_api_key=TEST_OPENAI_KEY,
        imap_username="mail-user",
        imap_password=TEST_IMAP_PASSWORD,
        smtp_password=TEST_SMTP_PASSWORD,
    )
    db_session.add(config)
    db_session.commit()

    # Query back to ensure it can be decrypted properly
    saved_config = (
        db_session.query(TenantConfig).filter_by(user_id="test_user2").first()
    )
    assert saved_config.openai_api_key == TEST_OPENAI_KEY

    # Verify that the value in the database is actually encrypted
    result = db_session.execute(
        text("SELECT openai_api_key FROM tenant_configs WHERE user_id='test_user2'")
    ).scalar()
    assert result != "test_key2"
    assert result is not None
    assert isinstance(result, str)

    imap_pw = db_session.execute(
        text("SELECT imap_password FROM tenant_configs WHERE user_id='test_user2'")
    ).scalar()
    smtp_pw = db_session.execute(
        text("SELECT smtp_password FROM tenant_configs WHERE user_id='test_user2'")
    ).scalar()
    assert imap_pw != TEST_IMAP_PASSWORD
    assert smtp_pw != TEST_SMTP_PASSWORD
    assert saved_config.imap_username == "mail-user"
    assert saved_config.imap_password == TEST_IMAP_PASSWORD
    assert saved_config.smtp_password == TEST_SMTP_PASSWORD

    # Verify __repr__ does not expose sensitive keys
    repr_str = repr(saved_config)
    assert TEST_OPENAI_KEY not in repr_str
    assert TEST_IMAP_PASSWORD not in repr_str
    assert TEST_SMTP_PASSWORD not in repr_str
    assert "has_openai_key=True" in repr_str
    assert "has_imap_password=True" in repr_str
    assert "has_smtp_password=True" in repr_str
