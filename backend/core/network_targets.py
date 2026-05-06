"""Validation helpers for tenant-configured outbound network destinations."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable


class MailTargetValidationError(ValueError):
    """Raised when a mail server target is not safe for outbound connections."""


AddressResolver = Callable[[str, int], list[str]]

MAIL_SERVICE_ALLOWED_PORTS: dict[str, set[int]] = {
    "smtp": {25, 465, 587, 2525},
    "imap": {143, 993},
    "pop3": {110, 995},
}


def validate_mail_server_target(
    host: str | None,
    port: int | None,
    service: str,
    resolver: AddressResolver | None = None,
) -> tuple[str, int]:
    """Validate a tenant-configured mail host and port before network use."""
    normalized_host = _normalize_mail_host(host)
    validated_port = _validate_mail_port(port, service)
    addresses = _resolve_host_addresses(normalized_host, validated_port, resolver)
    if not addresses:
        raise MailTargetValidationError("mail host did not resolve")
    for address in addresses:
        if not _is_public_ip_address(address):
            raise MailTargetValidationError(
                "mail host resolved to a restricted address"
            )
    return normalized_host, validated_port


def _normalize_mail_host(host: str | None) -> str:
    if host is None:
        raise MailTargetValidationError("mail host is required")

    normalized = host.strip().rstrip(".")
    if not normalized:
        raise MailTargetValidationError("mail host is required")
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]

    if _parse_ip_address(normalized) is not None:
        return normalized

    if any(char in normalized for char in ("/", "\\", "@", ":")):
        raise MailTargetValidationError("mail host must be a bare hostname")
    if any(ord(char) < 32 or char.isspace() for char in normalized):
        raise MailTargetValidationError("mail host contains invalid characters")

    try:
        ascii_host = normalized.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise MailTargetValidationError("mail host is not a valid hostname") from exc

    if not ascii_host or len(ascii_host) > 253:
        raise MailTargetValidationError("mail host length is invalid")

    labels = ascii_host.split(".")
    if any(not label or len(label) > 63 for label in labels):
        raise MailTargetValidationError("mail host label length is invalid")
    for label in labels:
        if label.startswith("-") or label.endswith("-"):
            raise MailTargetValidationError("mail host label format is invalid")
        if not all(char.isalnum() or char == "-" for char in label):
            raise MailTargetValidationError("mail host label format is invalid")
    return ascii_host.lower()


def _validate_mail_port(port: int | None, service: str) -> int:
    if port is None:
        raise MailTargetValidationError("mail port is required")
    try:
        validated_port = int(port)
    except (TypeError, ValueError) as exc:
        raise MailTargetValidationError("mail port must be an integer") from exc
    allowed_ports = MAIL_SERVICE_ALLOWED_PORTS.get(service)
    if allowed_ports is None:
        raise MailTargetValidationError("mail service is not supported")
    if validated_port not in allowed_ports:
        raise MailTargetValidationError("mail port is not allowed for this service")
    return validated_port


def _resolve_host_addresses(
    host: str,
    port: int,
    resolver: AddressResolver | None,
) -> list[str]:
    literal_address = _parse_ip_address(host)
    if literal_address is not None:
        return [str(literal_address)]

    if resolver is not None:
        return resolver(host, port)

    try:
        results = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise MailTargetValidationError("mail host did not resolve") from exc

    return sorted({str(result[4][0]) for result in results if result[4]})


def _is_public_ip_address(address: str) -> bool:
    parsed = _parse_ip_address(address)
    if parsed is None:
        return False
    if (
        parsed.is_loopback
        or parsed.is_private
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_unspecified
        or parsed.is_reserved
    ):
        return False
    return parsed.is_global


def _parse_ip_address(
    value: str,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None
