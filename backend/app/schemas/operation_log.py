from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class OperationLogOut(BaseModel):
    """Запись журнала операций. Никогда не содержит токены/заголовки/тела
    запросов."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    operation_type: str
    source: str | None
    status: str
    started_at: datetime.datetime
    finished_at: datetime.datetime | None
    date_from: datetime.date | None
    date_to: datetime.date | None
    records_processed: int | None
    report_id: int | None
    message: str | None
