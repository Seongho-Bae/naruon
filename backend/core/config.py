from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_email"
    DEBUG: bool = False
    
    # Email Client Settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    IMAP_SERVER: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    
    # OAuth Settings
    OAUTH_CLIENT_ID: str = ""
    OAUTH_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = ""
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
