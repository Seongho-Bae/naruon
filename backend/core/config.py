from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = False
    ENCRYPTION_KEY: SecretStr | None = None

    # OpenAI Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("DATABASE_URL")
    @classmethod
    def reject_default_postgres_credentials(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (parsed.username or "").lower() == "postgres" and (
            parsed.password or ""
        ).lower() == "postgres":
            raise ValueError(
                "DATABASE_URL must not use default PostgreSQL credentials"
            )
        return value


settings = Settings()
