import asyncio
import base64
import ipaddress
import logging
import socket
from email.message import EmailMessage
from typing import TypedDict, cast
from urllib.parse import urlsplit

import aiosmtplib
from aiosmtplib.errors import (
    SMTPConnectError,
    SMTPConnectResponseError,
    SMTPConnectTimeoutError,
    SMTPServerDisconnected,
    SMTPTimeoutError,
)
from aiosmtplib.protocol import SMTPProtocol
from aiosmtplib.status import SMTPStatus

from core.config import settings

logger = logging.getLogger(__name__)

SMTP_HOST_NOT_ALLOWED = "SMTP server is not allowed"
SMTP_PORT_NOT_ALLOWED = "SMTP port is not allowed"
SMTP_TIMEOUT_SECONDS = 60


def generate_oauth2_string(user: str, access_token: str) -> bytes:
    """Generates an OAuth2 string for IMAP/SMTP authentication."""
    auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode("utf-8"))


def _sanitize_log_value(value: str) -> str:
    """Remove CR/LF characters from user-provided values before logging."""
    return value.replace("\r", " ").replace("\n", " ")


def _parse_csv_values(value: str) -> set[str]:
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _parse_allowed_smtp_ports() -> set[int]:
    allowed_ports = set()
    for item in _parse_csv_values(settings.ALLOWED_SMTP_PORTS):
        try:
            allowed_ports.add(int(item))
        except ValueError:
            logger.warning("Ignoring invalid SMTP port policy entry")
    return allowed_ports


def _normalize_smtp_host(host: str) -> str:
    candidate = host.strip().lower().rstrip(".")
    if not candidate:
        raise ValueError(SMTP_HOST_NOT_ALLOWED)
    if any(character in candidate for character in " \t\r\n/"):
        raise ValueError(SMTP_HOST_NOT_ALLOWED)
    if "://" in candidate:
        parsed = urlsplit(candidate)
        candidate = (parsed.hostname or "").lower().rstrip(".")
    if not candidate or candidate in {"localhost", "localhost.localdomain"}:
        raise ValueError(SMTP_HOST_NOT_ALLOWED)
    return candidate


def _validate_public_ip_address(address: str) -> None:
    try:
        ip_address = ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValueError(SMTP_HOST_NOT_ALLOWED) from exc
    if not ip_address.is_global:
        raise ValueError(SMTP_HOST_NOT_ALLOWED)


def validate_smtp_host(host: str, *, resolve_host: bool) -> str:
    """Validate an outbound SMTP host against operator policy and SSRF guards."""
    normalized_host = _normalize_smtp_host(host)
    allowed_hosts = _parse_csv_values(settings.ALLOWED_SMTP_HOSTS)
    if not allowed_hosts or normalized_host not in allowed_hosts:
        raise ValueError(SMTP_HOST_NOT_ALLOWED)

    try:
        _validate_public_ip_address(normalized_host)
    except ValueError:
        if normalized_host.replace(".", "").isdigit() or ":" in normalized_host:
            raise

    if resolve_host:
        try:
            address_infos = socket.getaddrinfo(
                normalized_host, None, type=socket.SOCK_STREAM
            )
        except socket.gaierror as exc:
            raise ValueError(SMTP_HOST_NOT_ALLOWED) from exc
        for address_info in address_infos:
            sockaddr = address_info[4]
            _validate_public_ip_address(str(sockaddr[0]))
    return normalized_host


def validate_smtp_port(port: int) -> int:
    """Validate an outbound SMTP port against operator policy."""
    allowed_ports = _parse_allowed_smtp_ports()
    if port not in allowed_ports:
        raise ValueError(SMTP_PORT_NOT_ALLOWED)
    return port


def validate_smtp_destination(
    smtp_server: str,
    smtp_port: int,
    *,
    resolve_host: bool = True,
) -> tuple[str, int]:
    """Validate SMTP destination before any server-side network connection."""
    normalized_host = validate_smtp_host(smtp_server, resolve_host=resolve_host)
    validated_port = validate_smtp_port(smtp_port)
    return normalized_host, validated_port


async def _resolve_smtp_connect_address(
    smtp_server: str, smtp_port: int
) -> tuple[int, int, int, tuple]:
    """Resolve SMTP host once and return a globally-routable socket target."""
    loop = asyncio.get_running_loop()
    try:
        address_infos = await loop.getaddrinfo(
            smtp_server, smtp_port, type=socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        raise ValueError(SMTP_HOST_NOT_ALLOWED) from exc

    connect_address = None
    for address_info in address_infos:
        family, socktype, proto, _, sockaddr = address_info
        resolved_address = str(sockaddr[0])
        _validate_public_ip_address(resolved_address)
        connect_address = connect_address or (family, socktype, proto, sockaddr)
    if connect_address is None:
        raise ValueError(SMTP_HOST_NOT_ALLOWED)
    return connect_address


async def _connect_validated_smtp_socket(
    smtp_server: str, smtp_port: int
) -> socket.socket:
    """Connect a non-blocking socket to the already validated SMTP address."""
    family, socktype, proto, sockaddr = await _resolve_smtp_connect_address(
        smtp_server, smtp_port
    )
    smtp_socket = socket.socket(family, socktype, proto)
    smtp_socket.setblocking(False)
    try:
        await asyncio.wait_for(
            asyncio.get_running_loop().sock_connect(smtp_socket, sockaddr),
            timeout=SMTP_TIMEOUT_SECONDS,
        )
    except Exception:
        smtp_socket.close()
        raise
    return smtp_socket


class SendEmailResult(TypedDict):
    status: str
    simulated: bool


class _PinnedImplicitTlsSMTP(aiosmtplib.SMTP):
    """SMTP client that supplies SNI when TLS starts over a pinned socket."""

    def __init__(self, *, tls_server_hostname: str, **kwargs):
        self._tls_server_hostname = tls_server_hostname
        super().__init__(**kwargs)

    async def _create_connection(self, timeout: float | None):
        if self.loop is None:
            raise RuntimeError("No event loop set")
        smtp_socket = self.sock
        if not isinstance(smtp_socket, socket.socket) or not self.use_tls:
            return await super()._create_connection(timeout)
        smtp_socket = cast(socket.socket, smtp_socket)

        protocol = SMTPProtocol(loop=self.loop)
        tls_context = self._get_tls_context()
        connect_coro = self.loop.create_connection(
            lambda: protocol,
            sock=smtp_socket,
            ssl=tls_context,
            server_hostname=self._tls_server_hostname,
            ssl_handshake_timeout=timeout,
        )

        try:
            transport, _ = await asyncio.wait_for(connect_coro, timeout=timeout)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise SMTPConnectTimeoutError(
                f"Timed out connecting to {self._tls_server_hostname}"
            ) from exc
        except OSError as exc:
            raise SMTPConnectError(
                f"Error connecting to {self._tls_server_hostname}: {exc}"
            ) from exc

        self.protocol = protocol
        self.transport = transport

        try:
            response = await protocol.read_response(timeout=timeout)
        except SMTPServerDisconnected as exc:
            raise SMTPConnectError(
                f"Error connecting to {self._tls_server_hostname}: {exc}"
            ) from exc
        except SMTPTimeoutError as exc:
            raise SMTPConnectTimeoutError(
                "Timed out waiting for server ready message"
            ) from exc

        if response.code != SMTPStatus.ready:
            raise SMTPConnectResponseError(response.code, response.message)

        return response


def _build_smtp_client(
    *, smtp_socket: socket.socket, smtp_server: str, smtp_port: int
) -> aiosmtplib.SMTP:
    if smtp_port == 465:
        return _PinnedImplicitTlsSMTP(
            hostname=None,
            port=None,
            sock=smtp_socket,
            timeout=SMTP_TIMEOUT_SECONDS,
            use_tls=True,
            tls_server_hostname=smtp_server,
        )
    return aiosmtplib.SMTP(
        hostname=None,
        port=None,
        sock=smtp_socket,
        timeout=SMTP_TIMEOUT_SECONDS,
        start_tls=False,
    )


async def _send_pinned_smtp_message(
    message: EmailMessage,
    *,
    smtp_socket: socket.socket,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str | None,
    smtp_password: str | None,
) -> SendEmailResult:
    """Send through a pre-connected SMTP socket without a second DNS lookup."""
    try:
        client = _build_smtp_client(
            smtp_socket=smtp_socket,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
        )
        async with client:
            if smtp_port != 465:
                await client.starttls(server_hostname=smtp_server)
            if smtp_username is not None:
                await client.login(smtp_username, smtp_password or "")
            await client.send_message(message)
        return {"status": "sent", "simulated": False}
    finally:
        smtp_socket.close()


def build_email_message(
    to_address: str,
    subject: str,
    body: str,
    from_address: str,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> EmailMessage:
    """Build an outbound email message with optional threading headers."""
    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
    if references:
        message["References"] = references
    message.set_content(body)
    return message


async def send_email(
    to_address: str,
    subject: str,
    body: str,
    smtp_server: str | None = None,
    smtp_port: int | None = None,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> SendEmailResult:
    """Sends an email using SMTP."""
    safe_to_address = _sanitize_log_value(to_address)
    message = build_email_message(
        to_address=to_address,
        subject=subject,
        body=body,
        from_address=smtp_username or "me@example.com",
        in_reply_to=in_reply_to,
        references=references,
    )

    if not smtp_server or not smtp_port:
        logger.info(
            "Simulating sending email to %s (no SMTP server configured)",
            safe_to_address,
        )
        return {"status": "simulated", "simulated": True}

    smtp_server, smtp_port = validate_smtp_destination(
        smtp_server, smtp_port, resolve_host=False
    )

    try:
        smtp_socket = await _connect_validated_smtp_socket(smtp_server, smtp_port)
        try:
            result = await _send_pinned_smtp_message(
                message,
                smtp_socket=smtp_socket,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
            )
        finally:
            smtp_socket.close()
        logger.info(
            "Successfully sent email to %s via %s", safe_to_address, smtp_server
        )
        return result
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")
