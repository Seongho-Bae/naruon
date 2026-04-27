from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_email"
    DEBUG: bool = False
    
    # Email Client Settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    IMAP_SERVER: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    
    # OAuth Settings
    OAUTH_CLIENT_ID: str | None = None
    OAUTH_CLIENT_SECRET: SecretStr | None = None
    OAUTH_REDIRECT_URI: str | None = None
    
    # OpenAI Settings
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MODEL: str = "gpt-4o"
    
    # Google Calendar Settings
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: SecretStr | None = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
