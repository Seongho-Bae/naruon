from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_email"
    DEBUG: bool = False
    TRUST_DEV_HEADERS: bool = False
    ENCRYPTION_KEY: SecretStr | None = None
    AUTH_MODE: Literal["header", "hybrid", "oidc"] = "hybrid"
    OIDC_ISSUER: str | None = None
    OIDC_AUDIENCE: str | None = None
    OIDC_JWKS_URL: str | None = None
    OIDC_SHARED_SECRET: SecretStr | str | None = None
    LEGACY_LLM_PROVIDER_ORGANIZATION_ID: str | None = None
    LEGACY_EMAIL_OWNER_USER_ID: str | None = None

    # OpenAI Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
