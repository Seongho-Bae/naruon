from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = False
    ENCRYPTION_KEY: SecretStr
    # Local fixture/bootstrap owner default only; runtime auth uses signed tokens.
    API_AUTH_USER_ID: str | None = None
    API_AUTH_SIGNING_SECRET: SecretStr | None = None
    API_AUTH_SIGNING_SECRET_FILE: str | None = None
    EMAIL_SEND_RATE_LIMIT_WINDOW_SECONDS: int = 60
    EMAIL_SEND_MAX_PER_WINDOW: int = 10

    # OpenAI Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore[call-arg]
