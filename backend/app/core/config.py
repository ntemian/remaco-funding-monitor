from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Remaco EU Funding Monitor"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./funding_monitor.db"
    SYNC_DATABASE_URL: str = "sqlite:///./funding_monitor.db"

    # TED API
    TED_API_BASE: str = "https://api.ted.europa.eu/v3"

    # Funding & Tenders Portal
    FTOP_API_BASE: str = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"

    # Email digest
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    DIGEST_RECIPIENT: str = ""

    # Scheduler
    DAILY_SCAN_HOUR: int = 7
    DAILY_SCAN_MINUTE: int = 0

    # API key for MVP auth
    API_KEY: str = "remaco-dev-key"

    class Config:
        env_file = ".env"


settings = Settings()
