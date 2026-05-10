from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(...)
    DATABASE_URL_READ_ONLY: str | None = None
    DEBUG: bool = False
    ENCRYPTION_KEY: SecretStr | None = None
    API_AUTH_TOKEN: SecretStr | None = None
    AUTH_SINGLE_USER_ID: str = "default"
    ENABLE_API_BACKGROUND_WORKERS: bool = False
    DISABLE_BACKGROUND_WORKERS: bool = False
    OTEL_SERVICE_NAME: str = "naruon-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None
    OTEL_EXPORTER_OTLP_INSECURE: bool = True

    # OpenAI Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore[call-arg]
