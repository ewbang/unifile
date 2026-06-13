from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "UniFile"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "unifile-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    # Database
    DB_PATH: str = os.path.expanduser("~/.unifile/db/unifile.db")

    # Redis (optional)
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure DB directory exists
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
