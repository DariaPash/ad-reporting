from __future__ import annotations

import datetime
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.report import (
    Report,
    ReportCampaign,
    ReportDailyStatistic,
    ReportGoal,
)


@dataclass(frozen=True)
class ReportDailyRowIn:
    campaign_id: int
    stat_date: datetime.date
    impressions: int
    clicks: int
    cost: float
    conversions: int | None
    leads: int | None


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_summaries(self, limit: int = 50, offset: int = 0) -> list[Report]:
        stmt = (
            select(Report)
            .options(
                selectinload(Report.campaigns), selectinload(Report.goals)
            )
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.scalars(stmt))

    def get_detail(self, report_id: int) -> Report | None:
        stmt = (
            select(Report)
            .where(Report.id == report_id)
            .options(
                selectinload(Report.campaigns),
                selectinload(Report.goals),
                selectinload(Report.daily_statistics),
            )
        )
        return self._db.scalars(stmt).one_or_none()

    def create(
        self,
        date_from: datetime.date,
        date_to: datetime.date,
        campaigns: list[tuple[int, str]],
        goals: list[tuple[int, str, bool, bool]],
        daily_rows: list[ReportDailyRowIn],
    ) -> Report:
        """Одна транзакция: заголовок + снимки кампаний/целей + дневные факты.

        Принимает уже рассчитанные данные, к внешним API не обращается.
        """
        report = Report(date_from=date_from, date_to=date_to)
        self._db.add(report)
        self._db.flush()  # получить report.id для FK ниже

        for campaign_id, name_snapshot in campaigns:
            self._db.add(
                ReportCampaign(
                    report_id=report.id,
                    campaign_id=campaign_id,
                    campaign_name_snapshot=name_snapshot,
                )
            )
        for goal_id, name_snapshot, is_conversion, is_lead in goals:
            self._db.add(
                ReportGoal(
                    report_id=report.id,
                    goal_id=goal_id,
                    goal_name_snapshot=name_snapshot,
                    is_conversion_snapshot=is_conversion,
                    is_lead_snapshot=is_lead,
                )
            )
        for row in daily_rows:
            self._db.add(
                ReportDailyStatistic(
                    report_id=report.id,
                    campaign_id=row.campaign_id,
                    stat_date=row.stat_date,
                    impressions=row.impressions,
                    clicks=row.clicks,
                    cost=row.cost,
                    conversions=row.conversions,
                    leads=row.leads,
                )
            )
        return report
