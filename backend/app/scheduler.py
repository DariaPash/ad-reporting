"""Фоновая автосинхронизация справочников кампаний/целей.

Периодический поток внутри backend-процесса, без внешнего планировщика.
Выключен по умолчанию (ENABLE_SCHEDULED_SYNC): app.main.app импортируется
в тестах, и иначе поток обращался бы к реальным API Яндекса.
"""

from __future__ import annotations

import logging
import threading
import time

from app.clients.yandex_direct_client import YandexDirectClient
from app.clients.yandex_metrika_client import YandexMetrikaClient
from app.config import get_settings
from app.db.session import SessionLocal
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.statistics_repository import StatisticsRepository
from app.services.import_service import ImportService

logger = logging.getLogger(__name__)


def _run_sync_once() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        service = ImportService(
            db=db,
            direct_client=YandexDirectClient(
                token=settings.direct_token(),
                client_login=settings.direct_client_login or None,
            ),
            metrika_client=YandexMetrikaClient(token=settings.metrika_token()),
            campaign_repository=CampaignRepository(db),
            goal_repository=GoalRepository(db),
            statistics_repository=StatisticsRepository(db),
            operation_log_repository=OperationLogRepository(db),
            metrika_counter_id=settings.metrika_counter_id,
            metrika_attribution=settings.metrika_attribution,
        )
        campaigns_result = service.sync_campaigns()
        goals_result = service.sync_goals()
        logger.info(
            "scheduled sync done: campaigns +%s/~%s, goals +%s/~%s",
            campaigns_result.created,
            campaigns_result.updated,
            goals_result.created,
            goals_result.updated,
        )
    except (
        Exception
    ):  # noqa: BLE001 – фоновый поток не должен падать целиком из-за одной неудачной попытки
        logger.exception("scheduled sync failed")
    finally:
        db.close()


def _loop(interval_seconds: int) -> None:
    while True:
        _run_sync_once()
        time.sleep(interval_seconds)


def start_background_sync() -> None:
    settings = get_settings()
    if not settings.enable_scheduled_sync:
        return
    if not settings.metrika_counter_id:
        logger.warning(
            "scheduled sync enabled, but METRIKA_COUNTER_ID is empty"
            " — skipping"
        )
        return
    thread = threading.Thread(
        target=_loop,
        args=(settings.sync_interval_minutes * 60,),
        daemon=True,
        name="campaigns-goals-sync",
    )
    thread.start()
    logger.info(
        "scheduled sync thread started, interval=%s min",
        settings.sync_interval_minutes,
    )
