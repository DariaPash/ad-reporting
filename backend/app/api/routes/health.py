from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: DbSession) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except (
        Exception
    ):  # noqa: BLE001 – health endpoint обязан не падать, а сообщить статус
        database_status = "error"
    return HealthResponse(status="ok", database=database_status)
