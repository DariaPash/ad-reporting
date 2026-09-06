from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Report(Base):
    """Заголовок сформированного отчета - зафиксированный результат за
    период."""

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("date_from <= date_to", name="ck_reports_period"),
        # Обычный возрастающий индекс (не DESC) – для истории отчётов этого
        # достаточно.
        Index("ix_reports_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    date_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    date_to: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    campaigns: Mapped[list["ReportCampaign"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    goals: Mapped[list["ReportGoal"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    daily_statistics: Mapped[list["ReportDailyStatistic"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ReportCampaign(Base):
    """Ассоциативная сущность M:N Отчет <-> Кампания, со снимком названия."""

    __tablename__ = "report_campaigns"
    __table_args__ = (Index("ix_report_campaigns_campaign", "campaign_id"),)

    report_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("reports.id", onupdate="RESTRICT", ondelete="CASCADE"),
        primary_key=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("campaigns.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    campaign_name_snapshot: Mapped[str] = mapped_column(Text, nullable=False)

    report: Mapped[Report] = relationship(back_populates="campaigns")


class ReportGoal(Base):
    """Ассоциативная сущность M:N Отчет <-> Цель. Записей может не быть."""

    __tablename__ = "report_goals"
    __table_args__ = (Index("ix_report_goals_goal", "goal_id"),)

    report_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("reports.id", onupdate="RESTRICT", ondelete="CASCADE"),
        primary_key=True,
    )
    goal_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("goals.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        primary_key=True,
    )
    goal_name_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    is_conversion_snapshot: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    is_lead_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False)

    report: Mapped[Report] = relationship(back_populates="goals")


class ReportDailyStatistic(Base):
    """Снимок данных отчета по датам и кампаниям (неизменяемый после
    создания)."""

    __tablename__ = "report_daily_statistics"
    __table_args__ = (
        CheckConstraint(
            "impressions >= 0", name="ck_report_daily_statistics_impressions"
        ),
        CheckConstraint(
            "clicks >= 0", name="ck_report_daily_statistics_clicks"
        ),
        CheckConstraint("cost >= 0", name="ck_report_daily_statistics_cost"),
        CheckConstraint(
            "conversions IS NULL OR conversions >= 0",
            name="ck_report_daily_statistics_conversions",
        ),
        CheckConstraint(
            "leads IS NULL OR leads >= 0",
            name="ck_report_daily_statistics_leads",
        ),
    )

    report_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("reports.id", onupdate="RESTRICT", ondelete="CASCADE"),
        primary_key=True,
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
    conversions: Mapped[int | None] = mapped_column(BigInteger)
    leads: Mapped[int | None] = mapped_column(BigInteger)

    report: Mapped[Report] = relationship(back_populates="daily_statistics")
