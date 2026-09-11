from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.statistics import (
    DirectDailyStatistic,
    MetrikaDailyStatistic,
    MetrikaGoalDailyStatistic,
)


class StatisticsRepository:
    """Чтение и запись исходной дневной статистики (не снимка отчёта).

    Запись – одной транзакцией на партию, полученную от внешнего API. Чтение
    нужно, чтобы определить недостающие даты до обращения к внешним API.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def existing_direct_dates(
        self,
        campaign_id: int,
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> set[datetime.date]:
        stmt = select(DirectDailyStatistic.stat_date).where(
            DirectDailyStatistic.campaign_id == campaign_id,
            DirectDailyStatistic.stat_date.between(date_from, date_to),
        )
        return set(self._db.scalars(stmt))

    def existing_metrika_dates(
        self,
        campaign_id: int,
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> set[datetime.date]:
        stmt = select(MetrikaDailyStatistic.stat_date).where(
            MetrikaDailyStatistic.campaign_id == campaign_id,
            MetrikaDailyStatistic.stat_date.between(date_from, date_to),
        )
        return set(self._db.scalars(stmt))

    def existing_metrika_goal_dates(
        self,
        campaign_id: int,
        goal_id: int,
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> set[datetime.date]:
        stmt = select(MetrikaGoalDailyStatistic.stat_date).where(
            MetrikaGoalDailyStatistic.campaign_id == campaign_id,
            MetrikaGoalDailyStatistic.goal_id == goal_id,
            MetrikaGoalDailyStatistic.stat_date.between(date_from, date_to),
        )
        return set(self._db.scalars(stmt))

    def upsert_direct_daily(
        self,
        campaign_id: int,
        stat_date: datetime.date,
        impressions: int,
        clicks: int,
        cost: float,
    ) -> None:
        row = self._db.get(DirectDailyStatistic, (campaign_id, stat_date))
        if row is None:
            self._db.add(
                DirectDailyStatistic(
                    campaign_id=campaign_id,
                    stat_date=stat_date,
                    impressions=impressions,
                    clicks=clicks,
                    cost=cost,
                )
            )
        else:
            row.impressions, row.clicks, row.cost = impressions, clicks, cost

    def upsert_metrika_daily(
        self, campaign_id: int, stat_date: datetime.date, visits: int
    ) -> None:
        row = self._db.get(MetrikaDailyStatistic, (campaign_id, stat_date))
        if row is None:
            self._db.add(
                MetrikaDailyStatistic(
                    campaign_id=campaign_id, stat_date=stat_date, visits=visits
                )
            )
        else:
            row.visits = visits

    def upsert_metrika_goal_daily(
        self,
        campaign_id: int,
        goal_id: int,
        stat_date: datetime.date,
        goal_reaches: int,
    ) -> None:
        row = self._db.get(
            MetrikaGoalDailyStatistic, (campaign_id, goal_id, stat_date)
        )
        if row is None:
            self._db.add(
                MetrikaGoalDailyStatistic(
                    campaign_id=campaign_id,
                    goal_id=goal_id,
                    stat_date=stat_date,
                    goal_reaches=goal_reaches,
                )
            )
        else:
            row.goal_reaches = goal_reaches

    def get_direct_range(
        self,
        campaign_ids: list[int],
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> list[DirectDailyStatistic]:
        """Сырые факты Директа за период – для объединения источников перед
        расчётом KPI."""
        if not campaign_ids:
            return []
        stmt = select(DirectDailyStatistic).where(
            DirectDailyStatistic.campaign_id.in_(campaign_ids),
            DirectDailyStatistic.stat_date.between(date_from, date_to),
        )
        return list(self._db.scalars(stmt))

    def get_metrika_goal_range(
        self,
        campaign_ids: list[int],
        goal_ids: list[int],
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> list[MetrikaGoalDailyStatistic]:
        """Достижения целей Метрики за период. goal_ids – только выбранные
        пользователем цели."""
        if not campaign_ids or not goal_ids:
            return []
        stmt = select(MetrikaGoalDailyStatistic).where(
            MetrikaGoalDailyStatistic.campaign_id.in_(campaign_ids),
            MetrikaGoalDailyStatistic.goal_id.in_(goal_ids),
            MetrikaGoalDailyStatistic.stat_date.between(date_from, date_to),
        )
        return list(self._db.scalars(stmt))
