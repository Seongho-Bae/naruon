import ipaddress
import socket
from collections.abc import Mapping
from dataclasses import dataclass


class MailEndpointValidationError(ValueError):
    """Raised when a tenant-configured mail endpoint is unsafe to contact."""


@dataclass(frozen=True)
class SafeMailEndpoint:
    """A validated mail endpoint with resolver-pinned connection addresses."""

    host: str
    port: int | None
    addresses: tuple[str, ...]

    @property
    def connection_host(self) -> str:
        return self.addresses[0] if self.addresses else self.host


MAIL_PORTS_BY_SERVICE = {
    "smtp": {25, 465, 587},
    "imap": {143, 993},
    "pop3": {110, 995},
}

MAIL_ENDPOINT_FIELDS = (
    ("smtp", "smtp_server", "smtp_port"),
    ("imap", "imap_server", "imap_port"),
    ("pop3", "pop3_server", "pop3_port"),
)

LOCAL_HOSTNAMES = {"localhost", "localhost.localdomain"}
LOCAL_HOST_SUFFIXES = (".localhost", ".localdomain")


def assert_safe_mail_endpoint(
    host: str | None,
    port: int | None,
    *,
    service: str,
    resolve: bool = True,
) -> None:
    """Validate that a tenant-configured mail endpoint is safe to contact."""
    resolve_safe_mail_endpoint(host, port, service=service, resolve=resolve)


def resolve_safe_mail_endpoint(
    host: str | None,
    port: int | None,
    *,
    service: str,
    resolve: bool = True,
) -> SafeMailEndpoint:
    """Validate and return resolver-pinned addresses for an outbound mail endpoint."""
    if host is None and port is None:
        return SafeMailEndpoint(host="", port=None, addresses=())
    if port is not None and host is None:
        raise MailEndpointValidationError(
            f"{service} host is required when port is set"
        )

    normalized_host = _normalize_mail_host(host, service)
    if port is not None:
        _assert_allowed_mail_port(port, service)

    _assert_host_literal_is_public(normalized_host, service)
    addresses: tuple[str, ...] = ()
    if resolve:
        addresses = _resolve_public_addresses(normalized_host, port or 0, service)
    return SafeMailEndpoint(host=normalized_host, port=port, addresses=addresses)


def validate_mail_endpoints(
    values: Mapping[str, object | None],
    *,
    resolve: bool = True,
) -> None:
    """Validate all tenant mail endpoints present in a mapping of config values."""
    for service, host_field, port_field in MAIL_ENDPOINT_FIELDS:
        host = values.get(host_field)
        port = values.get(port_field)
        endpoint_should_be_validated = host is not None or port is not None
        if not endpoint_should_be_validated:
            continue
        assert_safe_mail_endpoint(
            str(host) if host is not None else None,
            int(port) if port is not None else None,
            service=service,
            resolve=resolve and port is not None,
        )


def _normalize_mail_host(host: str | None, service: str) -> str:
    if host is None:
        raise MailEndpointValidationError(f"{service} host is required")
    normalized = host.strip().lower()
    if not normalized:
        raise MailEndpointValidationError(f"{service} host is required")
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]
    if (
        "://" in normalized
        or "/" in normalized
        or "\\" in normalized
        or "@" in normalized
    ):
        raise MailEndpointValidationError(
            f"{service} host must be a hostname or IP address"
        )
    if "%" in normalized:
        raise MailEndpointValidationError(
            f"{service} host must not include an interface scope"
        )
    if normalized.endswith("."):
        normalized = normalized[:-1]
    return normalized


def _assert_allowed_mail_port(port: int, service: str) -> None:
    allowed_ports = MAIL_PORTS_BY_SERVICE.get(service)
    if allowed_ports is None:
        raise MailEndpointValidationError(f"Unsupported mail service: {service}")
    if port not in allowed_ports:
        allowed = ", ".join(str(item) for item in sorted(allowed_ports))
        raise MailEndpointValidationError(
            f"{service} port {port} is not allowed; allowed ports: {allowed}"
        )


def _assert_host_literal_is_public(host: str, service: str) -> None:
    if host in LOCAL_HOSTNAMES or host.endswith(LOCAL_HOST_SUFFIXES):
        raise MailEndpointValidationError(f"{service} host is not allowed")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    _assert_address_is_public(address, service)


def _resolve_public_addresses(host: str, port: int, service: str) -> tuple[str, ...]:
    try:
        resolved_addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise MailEndpointValidationError(
            f"{service} host could not be resolved"
        ) from exc

    if not resolved_addresses:
        raise MailEndpointValidationError(f"{service} host could not be resolved")

    public_addresses: list[str] = []
    for _, _, _, _, sockaddr in resolved_addresses:
        address_text = sockaddr[0]
        try:
            address = ipaddress.ip_address(address_text)
        except ValueError as exc:
            raise MailEndpointValidationError(
                f"{service} host resolved to an invalid address"
            ) from exc
        _assert_address_is_public(address, service)
        if address_text not in public_addresses:
            public_addresses.append(address_text)
    return tuple(public_addresses)


def _assert_address_is_public(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address, service: str
) -> None:
    if not address.is_global:
        raise MailEndpointValidationError(f"{service} host is not allowed")
