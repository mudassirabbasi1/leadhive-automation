from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Centralized settings loaded from environment variables.

    Beginner note: never hard-code passwords or API keys in source files.
    Copy backend/.env.example to backend/.env for local development.
    """

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / "backend" / ".env", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LeadHive Automation"
    app_env: str = "development"
    secret_key: str = Field(default="change-me-in-production", min_length=16)
    access_token_expire_minutes: int = 1440
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'database' / 'leadhive.db'}"
    frontend_origin: str = "http://localhost:5173"
    public_source_user_agent: str = "LeadHiveAutomation/1.0 contact@example.com"
    scraper_request_timeout: int = 20
    website_analysis_timeout: int = 12
    enable_playwright_analysis: bool = False
    email_sending_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "LeadHive Automation"
    email_rate_limit_per_hour: int = 20
    unsubscribe_text: str = (
        "If this is not relevant, reply with 'unsubscribe' and we will not contact you again."
    )
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

