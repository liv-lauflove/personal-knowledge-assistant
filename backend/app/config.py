from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str = "https://your-supabase-url.supabase.co"
    SUPABASE_KEY: str = "your-supabase-key"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
