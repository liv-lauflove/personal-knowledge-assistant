from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SUPABASE_URL: str = "https://your-supabase-url.supabase.co"
    SUPABASE_KEY: str = "your-supabase-key"
    FRONTEND_URL: str = "http://localhost:3000"


settings = Settings()
