from typing import Any, cast

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.runtime_secrets import (
    validate_auth_session_hmac_secret_value,
)
from core.url_validation import parse_allowed_hosts, validate_https_url_host


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
    ALLOWED_CORS_ORIGINS: str = ""
    ENABLE_PROMETHEUS_METRICS: bool = False
    SECURITY_CONTENT_SECURITY_POLICY: str = (
        "default-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    # OpenAI Settings
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


settings = Settings(**cast(dict[str, Any], {}))  # type: ignore
