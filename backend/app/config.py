from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    app_name: str = 'Request Tracker'
    app_debug: bool = True
    database_url: str = f"sqlite:///{BASE_DIR / 'tracker.db'}"
    REDIS_URL: str = "redis://localhost:6379/0"
    model_config = SettingsConfigDict(env_file=PROJECT_DIR / '.env')
    cors_origins: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()
