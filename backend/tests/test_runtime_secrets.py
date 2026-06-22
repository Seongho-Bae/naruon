import pytest
import math
from core.runtime_secrets import (
    _shannon_entropy_bits,
    _character_class_count,
    validate_auth_session_hmac_secret_value,
    _KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS,
    _LOW_ENTROPY_PLACEHOLDER_TERMS,
)


def test_shannon_entropy_bits():
    # A single repeated character has 0 entropy
    assert _shannon_entropy_bits("a") == 0.0
    assert _shannon_entropy_bits("aaaaa") == 0.0

    # 2 distinct characters with equal frequency
    assert math.isclose(_shannon_entropy_bits("ab"), 2.0)
    assert math.isclose(_shannon_entropy_bits("aabb"), 4.0)

    # 4 distinct characters with equal frequency
    assert math.isclose(_shannon_entropy_bits("abcd"), 8.0)

    # String with unequal frequencies
    # For 'aab': lengths=3, counts={'a': 2, 'b': 1}
    # -(2/3 * log2(2/3) + 1/3 * log2(1/3)) * 3
    # = -(2/3 * (1 - log2(3)) + 1/3 * (0 - log2(3))) * 3
    # = -(2/3 - 2/3 * log2(3) - 1/3 * log2(3)) * 3
    # = -(2/3 - log2(3)) * 3 = -2 + 3 * log2(3) = 3 * log2(3) - 2
    expected = 3 * math.log2(3) - 2
    assert math.isclose(_shannon_entropy_bits("aab"), expected)


def test_character_class_count():
    assert _character_class_count("a") == 1
    assert _character_class_count("A") == 1
    assert _character_class_count("1") == 1
    assert _character_class_count("!") == 1

    assert _character_class_count("aA") == 2
    assert _character_class_count("a1") == 2
    assert _character_class_count("a!") == 2

    assert _character_class_count("aA1") == 3
    assert _character_class_count("aA!") == 3

    assert _character_class_count("aA1!") == 4

    # Repeated characters shouldn't increase class count
    assert _character_class_count("aaAA11!!") == 4
    assert _character_class_count("abcDEF123!@#") == 4


def test_validate_auth_session_hmac_secret_value_valid():
    validate_auth_session_hmac_secret_value("thisisaverylongandsecurestring123!")


def test_validate_auth_session_hmac_secret_value_empty():
    with pytest.raises(
        ValueError,
        match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes",
    ):
        validate_auth_session_hmac_secret_value("")
    with pytest.raises(
        ValueError,
        match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes",
    ):
        validate_auth_session_hmac_secret_value(None)


def test_validate_auth_session_hmac_secret_value_short():
    with pytest.raises(
        ValueError,
        match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes",
    ):
        validate_auth_session_hmac_secret_value("short")
    with pytest.raises(
        ValueError,
        match="AUTH_SESSION_HMAC_SECRET must be at least 32 bytes",
    ):
        validate_auth_session_hmac_secret_value("a" * 31)


def test_validate_auth_session_hmac_secret_value_repeated():
    with pytest.raises(ValueError, match="must not be a repeated character"):
        validate_auth_session_hmac_secret_value("a" * 32)
    with pytest.raises(ValueError, match="must not be a repeated character"):
        validate_auth_session_hmac_secret_value("1" * 64)


def test_validate_auth_session_hmac_secret_value_rejects_low_diversity():
    with pytest.raises(ValueError, match="at least 12 distinct characters"):
        validate_auth_session_hmac_secret_value("abcabcabcabcabcabcabcabcabcabcab")
    with pytest.raises(ValueError, match="at least three character classes"):
        validate_auth_session_hmac_secret_value("abcdefghijklmnopqrstuvwxyzabcdef")
    with pytest.raises(ValueError, match="at least 128 bits of estimated entropy"):
        validate_auth_session_hmac_secret_value("aaaaaaaaaaaaaaaaaaaaABC123!@#xyz")


def test_validate_auth_session_hmac_secret_value_public_fixture():
    for public_fixture in _KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS:
        with pytest.raises(ValueError, match="must not use a public fixture value"):
            validate_auth_session_hmac_secret_value(public_fixture)


def test_validate_auth_session_hmac_secret_value_placeholder():
    for term in _LOW_ENTROPY_PLACEHOLDER_TERMS:
        with pytest.raises(ValueError, match="must not contain placeholder terms"):
            validate_auth_session_hmac_secret_value(
                f"this_is_a_sufficiently_long_prefix_for_testing_purposes_{term}"
            )


def test_validate_auth_session_hmac_secret_value_rejects_strix_fixture():
    with pytest.raises(ValueError, match="placeholder terms"):
        validate_auth_session_hmac_secret_value("NaRuOnSeCrEtToKeN1234567890abcdef")
