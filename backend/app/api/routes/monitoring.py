"""Панель администратора (admin-only): проверка доступности внешних API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import (
    DbSession,
    get_direct_client,
    get_metrika_client,
    get_operation_log_repository,
    require_admin,
)
from app.clients.yandex_direct_client import YandexDirectClient
from app.clients.yandex_metrika_client import YandexMetrikaClient
from app.core.exceptions import ExternalApiError
from app.repositories.operation_log_repository import OperationLogRepository
from app.schemas.monitoring import ApiCheckOut, ApiStatus

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(require_admin)],
)


def _check_direct(client: YandexDirectClient) -> ApiStatus:
    try:
        client.get_campaigns()
        return "ok"
    except ExternalApiError:
        return "error"


def _check_metrika(client: YandexMetrikaClient) -> ApiStatus:
    try:
        client.get_counters()
        return "ok"
    except ExternalApiError:
        return "error"


@router.post("/api-check", response_model=ApiCheckOut)
def check_api_availability(
    direct_client: Annotated[YandexDirectClient, Depends(get_direct_client)],
    metrika_client: Annotated[
        YandexMetrikaClient, Depends(get_metrika_client)
    ],
    operations: Annotated[
        OperationLogRepository, Depends(get_operation_log_repository)
    ],
    db: DbSession,
) -> ApiCheckOut:
    """Проверяет доступность Директа и Метрики; результат также пишется в
    журнал операций."""
    entry = operations.start(
        operation_type="Проверка доступности API", source="monitoring"
    )
    db.commit()  # "running" фиксируется сразу, до обращения к внешним API
    direct_status = _check_direct(direct_client)
    metrika_status = _check_metrika(metrika_client)
    overall = (
        "success"
        if direct_status == "ok" and metrika_status == "ok"
        else "error"
    )
    operations.finish(
        entry,
        status=overall,
        message=f"Директ: {direct_status}, Метрика: {metrika_status}.",
    )
    db.commit()
    return ApiCheckOut(direct=direct_status, metrika=metrika_status)
