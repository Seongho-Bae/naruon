import asyncio
import base64
import logging
from email.message import EmailMessage
from typing import TypedDict

import aiosmtplib
from aiosmtplib.smtp import (
    SMTPConnectError,
    SMTPConnectResponseError,
    SMTPConnectTimeoutError,
    SMTPProtocol,
    SMTPServerDisconnected,
    SMTPStatus,
    SMTPTimeoutError,
)

from services.mail_server_security import (
    MailServerConnectTarget,
    MailServerValidationError,
    resolve_mail_server_connect_target,
)

logger = logging.getLogger(__name__)


def generate_oauth2_string(user: str, access_token: str) -> bytes:
    """Generates an OAuth2 string for IMAP/SMTP authentication."""
    auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode("utf-8"))


def _sanitize_log_value(value: str) -> str:
    """Remove CR/LF characters from user-provided values before logging."""
    return value.replace("\r", " ").replace("\n", " ")


class SendEmailResult(TypedDict):
    status: str
    simulated: bool


class _PinnedSMTP(aiosmtplib.SMTP):
    def __init__(
        self,
        *,
        connect_host: str,
        tls_server_hostname: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._connect_host = connect_host
        self._tls_server_hostname = tls_server_hostname

    async def _create_connection(self, timeout: float | None):
        if self.loop is None:
            raise RuntimeError("No event loop set")

        protocol = SMTPProtocol(loop=self.loop)
        tls_context = None
        ssl_handshake_timeout = None
        if self.use_tls:
            tls_context = self._get_tls_context()
            ssl_handshake_timeout = timeout

        if self.sock is not None or self.socket_path is not None:
            return await super()._create_connection(timeout)
        if self.port is None:
            raise RuntimeError("No port provided; default should have been set")

        connect_coro = self.loop.create_connection(
            lambda: protocol,
            host=self._connect_host,
            port=self.port,
            ssl=tls_context,
            ssl_handshake_timeout=ssl_handshake_timeout,
            local_addr=self.source_address,
            server_hostname=(
                self._tls_server_hostname if tls_context is not None else None
            ),
        )

        try:
            transport, _ = await asyncio.wait_for(connect_coro, timeout=timeout)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise SMTPConnectTimeoutError(
                f"Timed out connecting to {self.hostname} on port {self.port}"
            ) from exc
        except OSError as exc:
            raise SMTPConnectError(
                f"Error connecting to {self.hostname} on port {self.port}: {exc}"
            ) from exc

        self.protocol = protocol
        self.transport = transport

        try:
            response = await protocol.read_response(timeout=timeout)
        except SMTPServerDisconnected as exc:
            raise SMTPConnectError(
                f"Error connecting to {self.hostname} on port {self.port}: {exc}"
            ) from exc
        except SMTPTimeoutError as exc:
            raise SMTPConnectTimeoutError(
                "Timed out waiting for server ready message"
            ) from exc

        if response.code != SMTPStatus.ready:
            raise SMTPConnectResponseError(response.code, response.message)

        return response


async def _send_message_via_validated_smtp(
    message: EmailMessage,
    target: MailServerConnectTarget,
    username: str | None,
    password: str | None,
) -> None:
    smtp = _PinnedSMTP(
        hostname=target.host,
        port=target.port,
        connect_host=target.connect_host,
        tls_server_hostname=target.host,
        use_tls=True,
        username=username,
        password=password,
    )
    try:
        await smtp.connect()
        await smtp.send_message(message)
    finally:
        if smtp.is_connected:
            await smtp.quit()


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

    try:
        try:
            target = resolve_mail_server_connect_target(
                "smtp", "SMTP", smtp_server, smtp_port
            )
        except MailServerValidationError as exc:
            raise Exception(str(exc)) from exc

        await _send_message_via_validated_smtp(
            message, target, smtp_username, smtp_password
        )
        logger.info(
            "Successfully sent email to %s via %s", safe_to_address, target.host
        )
        return {"status": "sent", "simulated": False}
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")
