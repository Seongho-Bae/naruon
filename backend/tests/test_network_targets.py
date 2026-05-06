import pytest

from core.network_targets import MailTargetValidationError, validate_mail_server_target


def test_validate_mail_server_target_allows_public_literal_ip():
    assert validate_mail_server_target("8.8.8.8", 587, "smtp") == ("8.8.8.8", 587)


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.0.1",
        "169.254.169.254",
        "::1",
        "fe80::1",
        "0.0.0.0",
    ],
)
def test_validate_mail_server_target_rejects_restricted_literal_addresses(host: str):
    with pytest.raises(MailTargetValidationError):
        validate_mail_server_target(host, 587, "smtp")


@pytest.mark.parametrize("host", ["http://127.0.0.1", "user@example.com", "host:587"])
def test_validate_mail_server_target_rejects_non_host_values(host: str):
    with pytest.raises(MailTargetValidationError):
        validate_mail_server_target(host, 587, "smtp")


@pytest.mark.parametrize(
    ("service", "port"),
    [("smtp", 80), ("imap", 587), ("pop3", 993)],
)
def test_validate_mail_server_target_rejects_ports_outside_mail_service_allowlist(
    service: str, port: int
):
    with pytest.raises(MailTargetValidationError):
        validate_mail_server_target("8.8.8.8", port, service)


def test_validate_mail_server_target_rejects_hostname_resolving_to_private_address():
    def resolver(host: str, port: int) -> list[str]:
        return ["10.0.0.1"]

    with pytest.raises(MailTargetValidationError):
        validate_mail_server_target("smtp.example.test", 587, "smtp", resolver=resolver)


def test_validate_mail_server_target_rejects_hostname_with_mixed_resolution():
    def resolver(host: str, port: int) -> list[str]:
        return ["8.8.8.8", "127.0.0.1"]

    with pytest.raises(MailTargetValidationError):
        validate_mail_server_target("smtp.example.test", 587, "smtp", resolver=resolver)


def test_validate_mail_server_target_allows_hostname_resolving_to_public_address():
    def resolver(host: str, port: int) -> list[str]:
        return ["8.8.8.8"]

    assert validate_mail_server_target(
        "SMTP.EXAMPLE.TEST.", 587, "smtp", resolver=resolver
    ) == ("smtp.example.test", 587)
