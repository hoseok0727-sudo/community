from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="Community Briefing API", alias="APP_NAME")
    env: str = Field(default="dev", alias="ENV")
    database_url: str = Field(
        default="sqlite:///./community_briefing.sqlite3",
        alias="DATABASE_URL",
    )
    collect_interval_minutes: int = Field(default=10, alias="COLLECT_INTERVAL_MINUTES")
    topic_window_hours: int = Field(default=24, alias="TOPIC_WINDOW_HOURS")
    default_fetch_limit: int = Field(default=100, alias="DEFAULT_FETCH_LIMIT")
    admin_api_key: str = Field(default="", alias="ADMIN_API_KEY")
    http_timeout_seconds: int = Field(default=12, alias="HTTP_TIMEOUT_SECONDS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
