from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog


class OperationLogRepository:
    """Безопасный журнал операций. Вызывающая сторона передаёт только
    безопасное сообщение – без токенов, заголовков Authorization и тел ответов
    внешних API.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def list(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[OperationLog]:
        stmt = (
            select(OperationLog)
            .order_by(OperationLog.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            stmt = stmt.where(OperationLog.status == status)
        return list(self._db.scalars(stmt))

    def start(
        self,
        operation_type: str,
        source: str | None = None,
        date_from: datetime.date | None = None,
        date_to: datetime.date | None = None,
    ) -> OperationLog:
        entry = OperationLog(
            operation_type=operation_type,
            source=source,
            status="running",
            date_from=date_from,
            date_to=date_to,
        )
        self._db.add(entry)
        self._db.flush()
        return entry

    def finish(
        self,
        entry: OperationLog,
        status: str,
        records_processed: int | None = None,
        report_id: int | None = None,
        message: str | None = None,
    ) -> OperationLog:
        entry.status = status
        entry.finished_at = datetime.datetime.now(datetime.timezone.utc)
        entry.records_processed = records_processed
        entry.report_id = report_id
        entry.message = message
        return entry
