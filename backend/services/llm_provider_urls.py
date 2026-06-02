import asyncio
import ipaddress
from dataclasses import dataclass
import socket
from urllib.parse import urlsplit, urlunsplit

import httpcore
import httpx
from httpcore._backends.auto import AutoBackend
from httpx._config import DEFAULT_LIMITS, create_ssl_context
from httpx._transports.default import AsyncResponseStream, map_httpcore_exceptions

from core.config import settings

LLM_BASE_URL_NOT_ALLOWED = "LLM provider base URL is not allowed"
_DNS_RESOLUTION_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class ValidatedLLMProviderBaseURL:
    normalized_url: str
    hostname: str
    port: int
    addresses: tuple[str, ...]


def _parse_allowed_hosts() -> set[str]:
    return {
        item.strip().lower().rstrip(".")
        for item in settings.ALLOWED_LLM_BASE_URL_HOSTS.split(",")
        if item.strip()
    }


def _is_ip_literal(candidate: str) -> bool:
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return True


def _looks_like_ip_literal(candidate: str) -> bool:
    compact_candidate = candidate.replace(".", "").lower()
    return (
        ":" in candidate
        or compact_candidate.isdigit()
        or compact_candidate.startswith("0x")
    )


def _validate_global_address(address: str) -> str:
    try:
        ip_address = ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED) from exc
    if (
        ip_address.is_private
        or ip_address.is_loopback
        or ip_address.is_link_local
        or ip_address.is_reserved
        or ip_address.is_unspecified
        or ip_address.is_multicast
        or not ip_address.is_global
    ):
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED)
    return str(ip_address)


def _resolve_all_global_addresses(hostname: str, port: int) -> tuple[str, ...]:
    try:
        address_infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED) from exc

    if not address_infos:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED)
    addresses: list[str] = []
    seen_addresses: set[str] = set()
    for address_info in address_infos:
        address = _validate_global_address(str(address_info[4][0]))
        if address not in seen_addresses:
            seen_addresses.add(address)
            addresses.append(address)
    return tuple(addresses)


async def _resolve_all_global_addresses_async(hostname: str, port: int) -> tuple[str, ...]:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_resolve_all_global_addresses, hostname, port),
            timeout=_DNS_RESOLUTION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED) from exc


def _normalize_llm_provider_base_url(value: str | None):
    if value is None:
        return None, None, None

    candidate = value.strip()
    if not candidate:
        return None, None, None

    try:
        parsed = urlsplit(candidate)
        port = parsed.port or 443
    except ValueError as exc:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED) from exc

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme.lower() != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or port != 443
        or hostname in {"localhost", "localhost.localdomain"}
    ):
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED)

    allowed_hosts = _parse_allowed_hosts()
    if not allowed_hosts or any("*" in allowed_host for allowed_host in allowed_hosts):
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED)
    if hostname not in allowed_hosts:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED)
    if _is_ip_literal(hostname) or _looks_like_ip_literal(hostname):
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED)

    netloc = hostname if parsed.port is None else f"{hostname}:{port}"
    return urlunsplit(("https", netloc, parsed.path or "", "", "")), hostname, port


def validate_llm_provider_base_url_details(
    value: str | None,
) -> ValidatedLLMProviderBaseURL | None:
    normalized_url, hostname, port = _normalize_llm_provider_base_url(value)
    if normalized_url is None:
        return None
    addresses = _resolve_all_global_addresses(hostname, port)
    return ValidatedLLMProviderBaseURL(normalized_url, hostname, port, addresses)


def validate_llm_provider_base_url(value: str | None) -> str | None:
    validated = validate_llm_provider_base_url_details(value)
    if validated is None:
        return None
    return validated.normalized_url


async def validate_llm_provider_base_url_details_async(
    value: str | None,
) -> ValidatedLLMProviderBaseURL | None:
    normalized_url, hostname, port = _normalize_llm_provider_base_url(value)
    if normalized_url is None:
        return None
    addresses = await _resolve_all_global_addresses_async(hostname, port)
    return ValidatedLLMProviderBaseURL(normalized_url, hostname, port, addresses)


async def validate_llm_provider_base_url_async(value: str | None) -> str | None:
    validated = await validate_llm_provider_base_url_details_async(value)
    if validated is None:
        return None
    return validated.normalized_url


class _PinnedLLMProviderNetworkBackend(httpcore.AsyncNetworkBackend):
    def __init__(self, hostname: str, port: int, addresses: tuple[str, ...]):
        if not addresses:
            raise ValueError(LLM_BASE_URL_NOT_ALLOWED)
        self._hostname = hostname
        self._port = port
        self._addresses = addresses
        self._backend = AutoBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options=None,
    ):
        host_text = host.decode("ascii") if isinstance(host, bytes) else str(host)
        normalized_host = host_text.lower().rstrip(".")
        if normalized_host != self._hostname or int(port) != self._port:
            raise OSError("LLM provider base URL host changed after validation")

        last_error: Exception | None = None
        for address in self._addresses:
            _validate_global_address(address)
            try:
                return await self._backend.connect_tcp(
                    address,
                    port,
                    timeout=timeout,
                    local_address=local_address,
                    socket_options=socket_options,
                )
            except Exception as exc:  # pragma: no cover - backend-specific
                last_error = exc
        if last_error is not None:
            raise last_error
        raise OSError(LLM_BASE_URL_NOT_ALLOWED)

    async def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options=None,
    ):
        raise OSError("LLM provider base URL must not use Unix sockets")

    async def sleep(self, seconds: float) -> None:
        await self._backend.sleep(seconds)


class _PinnedLLMProviderAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self, validated: ValidatedLLMProviderBaseURL):
        ssl_context = create_ssl_context(verify=True, trust_env=False)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=ssl_context,
            max_connections=DEFAULT_LIMITS.max_connections,
            max_keepalive_connections=DEFAULT_LIMITS.max_keepalive_connections,
            keepalive_expiry=DEFAULT_LIMITS.keepalive_expiry,
            http1=True,
            http2=False,
            network_backend=_PinnedLLMProviderNetworkBackend(
                validated.hostname,
                validated.port,
                validated.addresses,
            ),
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        req = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )
        with map_httpcore_exceptions():
            resp = await self._pool.handle_async_request(req)

        return httpx.Response(
            status_code=resp.status,
            headers=resp.headers,
            stream=AsyncResponseStream(resp.stream),
            extensions=resp.extensions,
        )

    async def aclose(self) -> None:
        await self._pool.aclose()


async def build_llm_provider_http_client(
    base_url: str | None,
) -> tuple[str | None, httpx.AsyncClient]:
    validated = await validate_llm_provider_base_url_details_async(base_url)
    if validated is None:
        return None, httpx.AsyncClient(follow_redirects=False, trust_env=False)
    return (
        validated.normalized_url,
        httpx.AsyncClient(
            follow_redirects=False,
            trust_env=False,
            transport=_PinnedLLMProviderAsyncTransport(validated),
        ),
    )
