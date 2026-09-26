from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import (
    auth,
    campaigns,
    goals,
    health,
    monitoring,
    operations,
    reports,
    users,
)
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.scheduler import start_background_sync


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Ad Reporting API",
        description=(
            "Веб-приложение автоматизации формирования отчётов по рекламным "
            "кампаниям (Яндекс Директ + Яндекс Метрика)."
        ),
        version="0.1.0",
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(campaigns.router)
    app.include_router(goals.router)
    app.include_router(reports.router)
    app.include_router(operations.router)
    app.include_router(users.router)
    app.include_router(monitoring.router)

    # no-op unless ENABLE_SCHEDULED_SYNC=true (см. app/scheduler.py)
    start_background_sync()

    return app


app = create_app()
