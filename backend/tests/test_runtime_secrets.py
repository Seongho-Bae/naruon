import pytest
from core.runtime_secrets import (
    validate_auth_session_hmac_secret_value,
    _KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS,
    _LOW_ENTROPY_PLACEHOLDER_TERMS
)

def test_validate_auth_session_hmac_secret_value_valid():
    validate_auth_session_hmac_secret_value("thisisaverylongandsecurestring123!")

def test_validate_auth_session_hmac_secret_value_empty():
    with pytest.raises(ValueError, match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes"):
        validate_auth_session_hmac_secret_value("")
    with pytest.raises(ValueError, match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes"):
        validate_auth_session_hmac_secret_value(None)

def test_validate_auth_session_hmac_secret_value_short():
    with pytest.raises(ValueError, match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes"):
        validate_auth_session_hmac_secret_value("short")
    with pytest.raises(ValueError, match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes"):
        validate_auth_session_hmac_secret_value("a" * 31)

def test_validate_auth_session_hmac_secret_value_repeated():
    with pytest.raises(ValueError, match="must not be a repeated character"):
        validate_auth_session_hmac_secret_value("a" * 32)
    with pytest.raises(ValueError, match="must not be a repeated character"):
        validate_auth_session_hmac_secret_value("1" * 64)

def test_validate_auth_session_hmac_secret_value_public_fixture():
    for public_fixture in _KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS:
        with pytest.raises(ValueError, match="must not use a public fixture value"):
            validate_auth_session_hmac_secret_value(public_fixture)

def test_validate_auth_session_hmac_secret_value_placeholder():
    for term in _LOW_ENTROPY_PLACEHOLDER_TERMS:
        with pytest.raises(ValueError, match="must not contain placeholder terms"):
            validate_auth_session_hmac_secret_value(f"this_is_a_sufficiently_long_prefix_for_testing_purposes_{term}")
