from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DEBUG: bool = False
    RUNTIME_ENVIRONMENT: str = "production"
    AUTH_SESSION_HMAC_SECRET: SecretStr | None = None
    ENCRYPTION_KEY: SecretStr | None = None
    CONTROL_PLANE_DOMAIN: str = "naruon.net"
    ALLOWED_SMTP_HOSTS: str = ""
    ALLOWED_SMTP_PORTS: str = "465,587"

    # OpenAI Settings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
