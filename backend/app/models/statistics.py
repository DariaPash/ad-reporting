from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DirectDailyStatistic(Base):
    """Факты Direct: одна запись на кампанию и календарную дату."""

    __tablename__ = "direct_daily_statistics"
    __table_args__ = (
        CheckConstraint(
            "impressions >= 0", name="ck_direct_daily_statistics_impressions"
        ),
        CheckConstraint(
            "clicks >= 0", name="ck_direct_daily_statistics_clicks"
        ),
        CheckConstraint("cost >= 0", name="ck_direct_daily_statistics_cost"),
        Index("ix_direct_daily_statistics_date", "stat_date"),
    )

    campaign_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    stat_date: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    impressions: Mapped[int] = mapped_column(BigInteger, nullable=False)
    clicks: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)


class MetrikaDailyStatistic(Base):
    """Визиты Метрики: не дублируются для каждой цели."""

    __tablename__ = "metrika_daily_statistics"
    __table_args__ = (
        CheckConstraint(
            "visits >= 0", name="ck_metrika_daily_statistics_visits"
        ),
        Index("ix_metrika_daily_statistics_date", "stat_date"),
    )

    campaign_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    stat_date: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    visits: Mapped[int] = mapped_column(BigInteger, nullable=False)


class MetrikaGoalDailyStatistic(Base):
    """Достижения целей: гранулярность кампания + цель + дата."""

    __tablename__ = "metrika_goal_daily_statistics"
    __table_args__ = (
        CheckConstraint(
            "goal_reaches >= 0",
            name="ck_metrika_goal_daily_statistics_reaches",
        ),
        Index("ix_metrika_goal_statistics_goal_date", "goal_id", "stat_date"),
    )

    campaign_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    goal_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("goals.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    stat_date: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    goal_reaches: Mapped[int] = mapped_column(BigInteger, nullable=False)
