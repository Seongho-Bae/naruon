from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


def parse_allowed_hosts(raw_hosts: str) -> frozenset[str]:
    hosts: set[str] = set()
    for raw_host in raw_hosts.split(","):
        host = _normalize_host(raw_host)
        if host:
            hosts.add(host)
    return frozenset(hosts)


def validate_https_url_host(
    setting_name: str,
    url_value: str,
    allowed_hosts: frozenset[str],
    allowed_hosts_setting_name: str,
) -> None:
    parsed = urlsplit(url_value)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"{setting_name} must use https")
    if parsed.username or parsed.password:
        raise ValueError(f"{setting_name} must not include userinfo")
    if parsed.fragment:
        raise ValueError(f"{setting_name} must not include a fragment")
    if not parsed.hostname:
        raise ValueError(f"{setting_name} must include a host")

    host = _normalize_host(parsed.hostname)
    if host not in allowed_hosts:
        raise ValueError(
            f"{setting_name} host must be listed in {allowed_hosts_setting_name}"
        )
    _reject_unsafe_ip_literal(setting_name, host)


def _normalize_host(raw_host: str) -> str:
    host = raw_host.strip().lower().rstrip(".")
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    return host


def _reject_unsafe_ip_literal(setting_name: str, host: str) -> None:
    try:
        ip_address = ipaddress.ip_address(host)
    except ValueError:
        if host == "localhost" or host.endswith(".localhost"):
            raise ValueError(f"{setting_name} host must not be localhost")
        return

    if not ip_address.is_global:
        raise ValueError(f"{setting_name} IP host must be globally routable")
