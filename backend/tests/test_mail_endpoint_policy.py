import socket

import pytest

from services.mail_endpoint_policy import (
    MailEndpointValidationError,
    assert_safe_mail_endpoint,
)


PUBLIC_RESOLVER_RESULTS = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 587))]


@pytest.mark.parametrize(
    "host",
    ["127.0.0.1", "localhost", "::1", "10.0.0.1", "169.254.169.254"],
)
def test_mail_endpoint_policy_rejects_loopback_private_and_link_local_hosts(host):
    with pytest.raises(MailEndpointValidationError, match="not allowed"):
        assert_safe_mail_endpoint(host, 587, service="smtp")


@pytest.mark.parametrize("port", [0, 1, 22, 80, 70000])
def test_mail_endpoint_policy_rejects_non_mail_smtp_ports(port):
    with pytest.raises(MailEndpointValidationError, match="port"):
        assert_safe_mail_endpoint("smtp.example.com", port, service="smtp", resolve=False)


def test_mail_endpoint_policy_rejects_public_hostname_that_resolves_private(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.1", 587))
        ],
    )

    with pytest.raises(MailEndpointValidationError, match="not allowed"):
        assert_safe_mail_endpoint("smtp.example.com", 587, service="smtp")


def test_mail_endpoint_policy_accepts_public_resolved_mail_host(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: PUBLIC_RESOLVER_RESULTS,
    )

    assert_safe_mail_endpoint("smtp.example.com", 587, service="smtp")
