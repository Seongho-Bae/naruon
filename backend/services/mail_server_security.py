import ipaddress
import socket
from dataclasses import dataclass

INTERNAL_MAIL_SERVER_MESSAGE = "메일 서버 주소는 내부 네트워크를 사용할 수 없습니다."

ALLOWED_MAIL_PORTS = {
    "smtp": {25, 465, 587, 2525},
    "imap": {143, 993},
    "pop3": {110, 995},
}


class MailServerValidationError(ValueError):
    """Raised when a user-configured mail server is unsafe to connect to."""


@dataclass(frozen=True)
class MailServerConnectTarget:
    """A validated mail endpoint with the exact IP to use for connection."""

    host: str
    port: int
    connect_host: str


def _is_internal_mail_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_multicast or not ip.is_global


def _validate_mail_server_syntax_and_port(
    prefix: str, label: str, host: str, port: int
) -> str:
    normalized_host = host.strip().rstrip(".").lower()
    if (
        not normalized_host
        or normalized_host in {"localhost", "localhost.localdomain"}
        or normalized_host.endswith(".localhost")
        or any(character in normalized_host for character in ("/", "\\", "@", "#"))
        or any(character.isspace() for character in normalized_host)
        or _is_internal_mail_ip(normalized_host)
    ):
        raise MailServerValidationError(INTERNAL_MAIL_SERVER_MESSAGE)

    allowed_ports = ALLOWED_MAIL_PORTS[prefix]
    if port not in allowed_ports:
        raise MailServerValidationError(
            f"{label} 포트는 허용된 메일 포트만 사용할 수 있습니다."
        )
    return normalized_host


def _resolve_safe_mail_server_ips(host: str, port: int) -> list[str]:
    try:
        resolved_addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return []

    safe_ips: list[str] = []
    for *_, sockaddr in resolved_addresses:
        resolved_ip = sockaddr[0]
        if _is_internal_mail_ip(resolved_ip):
            raise MailServerValidationError(INTERNAL_MAIL_SERVER_MESSAGE)
        safe_ips.append(resolved_ip)
    return safe_ips


def validate_mail_server_host(prefix: str, label: str, host: str, port: int) -> str:
    """Normalize and validate a mail server for persistence-time API checks."""
    normalized_host = _validate_mail_server_syntax_and_port(prefix, label, host, port)
    _resolve_safe_mail_server_ips(normalized_host, port)
    return normalized_host


def resolve_mail_server_connect_target(
    prefix: str, label: str, host: str, port: int
) -> MailServerConnectTarget:
    """Resolve and pin a safe mail server IP immediately before connecting."""
    normalized_host = _validate_mail_server_syntax_and_port(prefix, label, host, port)
    safe_ips = _resolve_safe_mail_server_ips(normalized_host, port)
    if not safe_ips:
        raise MailServerValidationError(f"{label} 서버 주소를 확인할 수 없습니다.")
    return MailServerConnectTarget(
        host=normalized_host,
        port=port,
        connect_host=safe_ips[0],
    )
