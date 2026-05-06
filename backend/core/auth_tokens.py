import base64
import binascii
import hashlib
import hmac
import json
import time
from secrets import compare_digest
from typing import Any


def _base64url_decode(value: str) -> bytes:
    """Decode an unpadded base64url value."""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def _base64url_encode(value: bytes) -> str:
    """Encode bytes as unpadded base64url text."""
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_json_segment(segment: str) -> dict[str, Any] | None:
    """Decode a compact token JSON segment."""
    try:
        decoded = _base64url_decode(segment)
        value = json.loads(decoded)
    except (binascii.Error, UnicodeError, json.JSONDecodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _signature_for(signing_input: str, signing_secret: str) -> str:
    """Return the expected compact-token HMAC signature."""
    signature = hmac.new(
        signing_secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return _base64url_encode(signature)


def _ascii_bytes(value: str) -> bytes | None:
    """Return ASCII bytes for compact-token material, or None when invalid."""
    try:
        return value.encode("ascii")
    except UnicodeError:
        return None


def verified_signed_subject(
    token: str, signing_secret: str, *, now: float | None = None
) -> str | None:
    """Return the token subject after signature and claim validation."""
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        return None

    header = _decode_json_segment(parts[0])
    payload = _decode_json_segment(parts[1])
    if header is None or payload is None:
        return None
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        return None

    signing_input = f"{parts[0]}.{parts[1]}"
    expected_signature = _signature_for(signing_input, signing_secret)
    token_signature = _ascii_bytes(parts[2])
    expected_signature_bytes = _ascii_bytes(expected_signature)
    if token_signature is None or expected_signature_bytes is None:
        return None
    if not compare_digest(token_signature, expected_signature_bytes):
        return None

    current_time = time.time() if now is None else now
    expires_at = payload.get("exp")
    if not isinstance(expires_at, (int, float)) or expires_at <= current_time:
        return None

    not_before = payload.get("nbf")
    if not_before is not None and (
        not isinstance(not_before, (int, float)) or not_before > current_time
    ):
        return None

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        return None
    return subject.strip()


def create_signed_auth_token(
    subject: str, signing_secret: str, *, ttl_seconds: int = 3600
) -> str:
    """Create a compact signed bearer token for local tooling and tests."""
    issued_at = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "iat": issued_at, "exp": issued_at + ttl_seconds}
    signing_input = ".".join(
        [
            _base64url_encode(json.dumps(header, separators=(",", ":")).encode()),
            _base64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
        ]
    )
    return f"{signing_input}.{_signature_for(signing_input, signing_secret)}"
