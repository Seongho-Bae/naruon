import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit

from core.config import settings

LLM_BASE_URL_NOT_ALLOWED = "LLM provider base URL is not allowed"
_DNS_RESOLUTION_TIMEOUT_SECONDS = 5.0


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


def _validate_global_address(address: str) -> None:
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


def _resolve_all_global_addresses(hostname: str, port: int) -> None:
    try:
        address_infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED) from exc

    if not address_infos:
        raise ValueError(LLM_BASE_URL_NOT_ALLOWED)
    for address_info in address_infos:
        _validate_global_address(str(address_info[4][0]))


async def _resolve_all_global_addresses_async(hostname: str, port: int) -> None:
    try:
        await asyncio.wait_for(
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


def validate_llm_provider_base_url(value: str | None) -> str | None:
    normalized_url, hostname, port = _normalize_llm_provider_base_url(value)
    if normalized_url is None:
        return None
    _resolve_all_global_addresses(hostname, port)
    return normalized_url


async def validate_llm_provider_base_url_async(value: str | None) -> str | None:
    normalized_url, hostname, port = _normalize_llm_provider_base_url(value)
    if normalized_url is None:
        return None
    await _resolve_all_global_addresses_async(hostname, port)
    return normalized_url
