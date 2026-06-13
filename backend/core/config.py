from typing import Any, cast
from urllib.parse import urlsplit

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.runtime_secrets import (
    validate_auth_session_hmac_secret_value,
)
from core.url_validation import parse_allowed_hosts, validate_https_url_host

DEFAULT_ORIGIN_PORTS = {
    "http": 80,
    "https": 443,
}


def canonical_origin(scheme: str, hostname: str, port: int | None) -> str:
    normalized_scheme = scheme.lower()
    normalized_host = hostname.lower()
    if ":" in normalized_host and not normalized_host.startswith("["):
        normalized_host = f"[{normalized_host}]"
    default_port = DEFAULT_ORIGIN_PORTS.get(normalized_scheme)
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{normalized_scheme}://{normalized_host}{port_suffix}"


def parse_allowed_cors_origins(raw_origins: str) -> list[str]:
    origins: list[str] = []
    for raw_origin in raw_origins.split(","):
        origin = raw_origin.strip()
        if not origin:
            continue
        if "*" in origin:
            raise ValueError("ALLOWED_CORS_ORIGINS must not include wildcards")

        parsed = urlsplit(origin)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("ALLOWED_CORS_ORIGINS entries must use http or https")
        if parsed.username or parsed.password:
            raise ValueError("ALLOWED_CORS_ORIGINS entries must not include userinfo")
        if not parsed.netloc or not parsed.hostname:
            raise ValueError("ALLOWED_CORS_ORIGINS entries must include a host")
        if parsed.path or parsed.query or parsed.fragment:
            raise ValueError(
                "ALLOWED_CORS_ORIGINS entries must be origins without path, query, or fragment"
            )
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError(
                "ALLOWED_CORS_ORIGINS entries must include a valid port"
            ) from exc

        origins.append(canonical_origin(parsed.scheme, parsed.hostname, port))
    return origins


class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = False
    RUNTIME_ENVIRONMENT: str = "production"
    AUTH_SESSION_HMAC_SECRET: SecretStr | None = None
    ENCRYPTION_KEY: SecretStr | None = None
    CONTROL_PLANE_DOMAIN: str = "naruon.net"
    ALLOWED_SMTP_HOSTS: str = ""
    ALLOWED_SMTP_PORTS: str = "465,587"
    ALLOWED_IMAP_HOSTS: str = ""
    ALLOWED_IMAP_PORTS: str = "993"
    ALLOWED_POP3_HOSTS: str = ""
    ALLOWED_POP3_PORTS: str = "995"
    ALLOWED_LLM_BASE_URL_HOSTS: str = ""
    ALLOW_LOCAL_LLM_PROVIDERS: bool = False
    ALLOWED_CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
    )
    ENABLE_PROMETHEUS_METRICS: bool = False
    DATA_REGION: str = "kr"
    SECONDARY_DATA_REGION: str = "eu"
    SECURITY_CONTENT_SECURITY_POLICY: str = (
        "default-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    # OpenAI Settings
    OPENAI_BASE_URL: str | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    # OIDC Settings
    OIDC_ISSUER_URL: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_JWKS_URL: str | None = None
    ALLOWED_OIDC_HOSTS: str = ""

    model_config = SettingsConfigDict(
        env_file=("~/.env", "../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_session_secret(self) -> "Settings":
        parse_allowed_cors_origins(self.ALLOWED_CORS_ORIGINS)

        configured = self.AUTH_SESSION_HMAC_SECRET
        if configured is None:
            raise ValueError(
                "AUTH_SESSION_HMAC_SECRET is required in all runtime environments"
            )

        validate_auth_session_hmac_secret_value(configured.get_secret_value())
        oidc_values = {
            "OIDC_ISSUER_URL": self.OIDC_ISSUER_URL,
            "OIDC_CLIENT_ID": self.OIDC_CLIENT_ID,
            "OIDC_JWKS_URL": self.OIDC_JWKS_URL,
        }
        configured_oidc_values = {
            setting_name: setting_value
            for setting_name, setting_value in oidc_values.items()
            if setting_value
        }
        if configured_oidc_values and len(configured_oidc_values) != len(oidc_values):
            raise ValueError(
                "OIDC_ISSUER_URL, OIDC_CLIENT_ID, and OIDC_JWKS_URL must be set together"
            )
        if len(configured_oidc_values) == len(oidc_values):
            allowed_oidc_hosts = parse_allowed_hosts(self.ALLOWED_OIDC_HOSTS)
            if not allowed_oidc_hosts:
                raise ValueError(
                    "ALLOWED_OIDC_HOSTS must list trusted OIDC issuer and JWKS hosts"
                )
            validate_https_url_host(
                "OIDC_ISSUER_URL",
                self.OIDC_ISSUER_URL or "",
                allowed_oidc_hosts,
                "ALLOWED_OIDC_HOSTS",
            )
            validate_https_url_host(
                "OIDC_JWKS_URL",
                self.OIDC_JWKS_URL or "",
                allowed_oidc_hosts,
                "ALLOWED_OIDC_HOSTS",
            )
        return self

    @property
    def ALLOWED_CORS_ORIGINS_LIST(self) -> list[str]:
        return parse_allowed_cors_origins(self.ALLOWED_CORS_ORIGINS)


settings = Settings(**cast(dict[str, Any], {}))  # type: ignore
