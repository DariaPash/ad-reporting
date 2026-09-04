"""Конфигурация backend из переменных окружения / .env. Секреты в БД не
хранятся."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень репозитория (backend/app/config.py -> ../../)
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    postgres_db: str = "ad_reporting"
    postgres_user: str = "ad_reporting"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "INFO"

    # Yandex APIs
    yandex_oauth_token: str = ""
    yandex_direct_token: str = ""
    yandex_metrika_token: str = ""
    direct_client_login: str = ""
    metrika_counter_id: str = ""
    metrika_attribution: str = "automatic"

    # Bootstrap-администратор: создаётся при первом запуске, если задан
    # и такого username ещё нет (см. app/bootstrap.py).
    initial_admin_username: str = ""
    initial_admin_password: str = ""

    # Фоновая автосинхронизация кампаний/целей (app/scheduler.py).
    # По умолчанию выключена, чтобы тесты не обращались к реальным API.
    enable_scheduled_sync: bool = False
    sync_interval_minutes: int = 30

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def direct_token(self) -> str:
        return self.yandex_direct_token or self.yandex_oauth_token

    def metrika_token(self) -> str:
        return self.yandex_metrika_token or self.yandex_oauth_token


@lru_cache
def get_settings() -> Settings:
    return Settings()
