from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'success', 'error')",
            name="ck_operation_logs_status",
        ),
        CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_operation_logs_finished_after_started",
        ),
        CheckConstraint(
            "date_from IS NULL OR date_to IS NULL OR date_from <= date_to",
            name="ck_operation_logs_period",
        ),
        CheckConstraint(
            "records_processed IS NULL OR records_processed >= 0",
            name="ck_operation_logs_records_processed",
        ),
        Index("ix_operation_logs_started_at", "started_at"),
        Index("ix_operation_logs_status_started_at", "status", "started_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    operation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    date_from: Mapped[datetime.date | None] = mapped_column(Date)
    date_to: Mapped[datetime.date | None] = mapped_column(Date)
    records_processed: Mapped[int | None] = mapped_column(Integer)
    report_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("reports.id", onupdate="RESTRICT", ondelete="SET NULL"),
    )
    message: Mapped[str | None] = mapped_column(Text)
