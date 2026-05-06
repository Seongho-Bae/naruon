from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = False
    ENCRYPTION_KEY: SecretStr
    API_AUTH_USER_ID: str | None = None
    API_AUTH_BEARER_TOKEN: SecretStr | None = None
    API_AUTH_BEARER_TOKEN_FILE: str | None = None

    # OpenAI Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore[call-arg]
