import socket
from unittest.mock import patch

import pytest

from core.url_validation import (
    ValidatedHTTPSURLHost,
    _normalize_host,
    _reject_unsafe_ip_literal,
    _resolve_global_addresses,
    _validate_global_address,
    parse_allowed_hosts,
    validate_https_url_host,
    validate_https_url_host_details,
)


def test_normalize_host():
    assert _normalize_host("  EXAMPLE.COM  ") == "example.com"
    assert _normalize_host("example.com.") == "example.com"
    assert _normalize_host("[2001:db8::1]") == "2001:db8::1"
    assert _normalize_host("  [2001:DB8::1].  ") == "2001:db8::1"


def test_parse_allowed_hosts():
    assert parse_allowed_hosts("example.com, TEST.ORG. , ") == frozenset(
        ["example.com", "test.org"]
    )
    assert parse_allowed_hosts("") == frozenset()


def test_reject_unsafe_ip_literal():
    # Localhosts
    with pytest.raises(ValueError, match="test_setting host must not be localhost"):
        _reject_unsafe_ip_literal("test_setting", "localhost")
    with pytest.raises(ValueError, match="test_setting host must not be localhost"):
        _reject_unsafe_ip_literal("test_setting", "sub.localhost")

    # Non-global IP
    with pytest.raises(
        ValueError, match="test_setting IP host must be globally routable"
    ):
        _reject_unsafe_ip_literal("test_setting", "127.0.0.1")
    with pytest.raises(
        ValueError, match="test_setting IP host must be globally routable"
    ):
        _reject_unsafe_ip_literal("test_setting", "10.0.0.1")
    with pytest.raises(
        ValueError, match="test_setting IP host must be globally routable"
    ):
        _reject_unsafe_ip_literal("test_setting", "::1")

    # Valid IP (assuming 8.8.8.8 is considered global by ipaddress)
    _reject_unsafe_ip_literal("test_setting", "8.8.8.8")
    _reject_unsafe_ip_literal("test_setting", "2001:4860:4860::8888")

    # Valid domain names (not IP) shouldn't raise exception here
    _reject_unsafe_ip_literal("test_setting", "example.com")


def test_validate_global_address():
    # Valid global
    assert _validate_global_address("test_setting", "8.8.8.8") == "8.8.8.8"
    assert (
        _validate_global_address("test_setting", "2001:4860:4860::8888")
        == "2001:4860:4860::8888"
    )

    # Invalid string
    with pytest.raises(
        ValueError, match="test_setting resolved IP host must be globally routable"
    ):
        _validate_global_address("test_setting", "not-an-ip")

    # Non-global IP
    with pytest.raises(
        ValueError, match="test_setting resolved IP host must be globally routable"
    ):
        _validate_global_address("test_setting", "127.0.0.1")


@patch("core.url_validation.socket.getaddrinfo")
def test_resolve_global_addresses(mock_getaddrinfo):
    # Mock return values for getaddrinfo
    # format: (family, type, proto, canonname, sockaddr)
    # sockaddr for IPv4 is (address, port)
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.4.4", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),  # duplicate
    ]

    addresses = _resolve_global_addresses("test_setting", "example.com", 443)
    assert addresses == ("8.8.8.8", "8.8.4.4")
    mock_getaddrinfo.assert_called_once_with(
        "example.com", 443, type=socket.SOCK_STREAM
    )

    # Test gaierror
    mock_getaddrinfo.reset_mock()
    mock_getaddrinfo.side_effect = socket.gaierror("test error")
    with pytest.raises(
        ValueError, match="test_setting host must resolve to a global address"
    ):
        _resolve_global_addresses("test_setting", "example.com", 443)

    # Test resolving to only local/non-global addresses
    mock_getaddrinfo.side_effect = None
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
    ]
    with pytest.raises(
        ValueError, match="test_setting resolved IP host must be globally routable"
    ):
        _resolve_global_addresses("test_setting", "example.com", 443)

    # Test resolving to empty list
    mock_getaddrinfo.return_value = []
    with pytest.raises(
        ValueError, match="test_setting host must resolve to a global address"
    ):
        _resolve_global_addresses("test_setting", "example.com", 443)


@patch("core.url_validation._resolve_global_addresses")
def test_validate_https_url_host_details(mock_resolve):
    mock_resolve.return_value = ("8.8.8.8",)
    allowed_hosts = frozenset(["example.com", "test.org"])

    # Success case - standard port
    res = validate_https_url_host_details(
        "test_setting", "https://example.com/path", allowed_hosts, "allowed_setting"
    )
    assert isinstance(res, ValidatedHTTPSURLHost)
    assert res.normalized_url == "https://example.com/path"
    assert res.hostname == "example.com"
    assert res.port == 443
    assert res.addresses == ("8.8.8.8",)

    # Success case - explicit port
    res = validate_https_url_host_details(
        "test_setting",
        "https://example.com:8443/path",
        allowed_hosts,
        "allowed_setting",
    )
    assert res.normalized_url == "https://example.com:8443/path"
    assert res.hostname == "example.com"
    assert res.port == 8443

    # Failures
    with pytest.raises(ValueError, match="test_setting must use https"):
        validate_https_url_host_details(
            "test_setting", "http://example.com", allowed_hosts, "allowed_setting"
        )

    with pytest.raises(ValueError, match="test_setting must not include userinfo"):
        validate_https_url_host_details(
            "test_setting",
            "https://user:pass@example.com",
            allowed_hosts,
            "allowed_setting",
        )

    with pytest.raises(ValueError, match="test_setting must not include a fragment"):
        validate_https_url_host_details(
            "test_setting",
            "https://example.com#fragment",
            allowed_hosts,
            "allowed_setting",
        )

    with pytest.raises(ValueError, match="test_setting must include a host"):
        validate_https_url_host_details(
            "test_setting", "https://", allowed_hosts, "allowed_setting"
        )

    with pytest.raises(
        ValueError, match="test_setting host must be listed in allowed_setting"
    ):
        validate_https_url_host_details(
            "test_setting",
            "https://notallowed.com",
            allowed_hosts,
            "allowed_setting",
        )


@patch("core.url_validation.validate_https_url_host_details")
def test_validate_https_url_host(mock_details):
    allowed_hosts = frozenset(["example.com"])
    validate_https_url_host(
        "test_setting", "https://example.com", allowed_hosts, "allowed_setting"
    )
    mock_details.assert_called_once_with(
        "test_setting", "https://example.com", allowed_hosts, "allowed_setting"
    )
