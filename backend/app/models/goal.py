from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Goal(Base):
    """Цель Яндекс Метрики и её бизнес-классификация (макро/микро)."""

    __tablename__ = "goals"
    __table_args__ = (
        UniqueConstraint(
            "counter_id",
            "metrika_goal_id",
            name="uq_goals_counter_external_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    counter_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metrika_goal_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    goal_type: Mapped[str | None] = mapped_column(String(64))
    is_conversion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_lead: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
