MIN_AUTH_SESSION_HMAC_SECRET_BYTES = 32
_LOW_ENTROPY_PLACEHOLDER_TERMS = ("change", "example", "password", "secret")
_KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS = frozenset(
    {"naruon-session-hmac-token-32-byte-minimum"}
)


def validate_auth_session_hmac_secret_value(secret: str) -> None:
    secret_bytes = secret.encode("utf-8")
    if len(secret_bytes) < MIN_AUTH_SESSION_HMAC_SECRET_BYTES:
        raise ValueError(
            "AUTH_SESSION_HMAC_SECRET must be at least 32 bytes in all environments"
        )
    if len(set(secret)) == 1:
        raise ValueError("AUTH_SESSION_HMAC_SECRET must not be a repeated character")
    normalized_secret = secret.lower()
    if normalized_secret in _KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS:
        raise ValueError("AUTH_SESSION_HMAC_SECRET must not use a public fixture value")
    if any(term in normalized_secret for term in _LOW_ENTROPY_PLACEHOLDER_TERMS):
        raise ValueError("AUTH_SESSION_HMAC_SECRET must not contain placeholder terms")
