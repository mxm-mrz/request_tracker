from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = 'Request Tracker'
    debug: bool = True
    database_url: str = f"sqlite:///{BASE_DIR / 'backend' / 'tracker.db'}"
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env')
    cors_origins: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
