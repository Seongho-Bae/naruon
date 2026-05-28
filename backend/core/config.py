from typing import Any, cast

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_AUTH_SESSION_HMAC_SECRET_BYTES = 32
_LOW_ENTROPY_PLACEHOLDER_TERMS = ("change", "example", "password", "secret")
_KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS = frozenset(
    {"naruon-session-hmac-token-32-byte-minimum"}
)


def validate_auth_session_hmac_secret_value(secret: str) -> None:
    secret_bytes = secret.encode("utf-8")
    if len(secret_bytes) < MIN_AUTH_SESSION_HMAC_SECRET_BYTES:
        raise ValueError(
            "AUTH_SESSION_HMAC_SECRET must be at least 32 bytes in all environments"
        )
    if len(set(secret)) == 1:
        raise ValueError("AUTH_SESSION_HMAC_SECRET must not be a repeated character")
    normalized_secret = secret.lower()
    if normalized_secret in _KNOWN_PUBLIC_AUTH_SESSION_HMAC_SECRETS:
        raise ValueError("AUTH_SESSION_HMAC_SECRET must not use a public fixture value")
    if any(term in normalized_secret for term in _LOW_ENTROPY_PLACEHOLDER_TERMS):
        raise ValueError("AUTH_SESSION_HMAC_SECRET must not contain placeholder terms")


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
    ENABLE_PROMETHEUS_METRICS: bool = False

    # OpenAI Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    # OIDC Settings
    OIDC_ISSUER_URL: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_JWKS_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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
        return self


settings = Settings(**cast(dict[str, Any], {}))  # type: ignore
