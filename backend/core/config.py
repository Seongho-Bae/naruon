from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_email"
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
