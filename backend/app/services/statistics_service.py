"""Проверка полноты и объединение уже сохранённой исходной статистики (только
чтение из БД)."""

from __future__ import annotations

import datetime
from collections import defaultdict
from dataclasses import dataclass

from app.models.goal import Goal
from app.repositories.report_repository import ReportDailyRowIn
from app.repositories.statistics_repository import StatisticsRepository


def _all_dates(
    date_from: datetime.date, date_to: datetime.date
) -> set[datetime.date]:
    days = (date_to - date_from).days
    return {date_from + datetime.timedelta(days=i) for i in range(days + 1)}


@dataclass(frozen=True)
class MissingRanges:
    direct_campaign_ids: set[int]
    metrika_campaign_ids: set[int]
    metrika_goal_pairs: set[tuple[int, int]]

    @property
    def is_complete(self) -> bool:
        return not (
            self.direct_campaign_ids
            or self.metrika_campaign_ids
            or self.metrika_goal_pairs
        )


class StatisticsService:
    def __init__(self, statistics_repository: StatisticsRepository) -> None:
        self._statistics = statistics_repository

    def find_missing(
        self,
        campaign_ids: list[int],
        goal_ids: list[int],
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> MissingRanges:
        required_dates = _all_dates(date_from, date_to)

        missing_direct: set[int] = set()
        missing_metrika: set[int] = set()
        for campaign_id in campaign_ids:
            if (
                self._statistics.existing_direct_dates(
                    campaign_id, date_from, date_to
                )
                != required_dates
            ):
                missing_direct.add(campaign_id)
            if (
                goal_ids
                and self._statistics.existing_metrika_dates(
                    campaign_id, date_from, date_to
                )
                != required_dates
            ):
                missing_metrika.add(campaign_id)

        missing_goal_pairs: set[tuple[int, int]] = set()
        for campaign_id in campaign_ids:
            for goal_id in goal_ids:
                existing = self._statistics.existing_metrika_goal_dates(
                    campaign_id, goal_id, date_from, date_to
                )
                if existing != required_dates:
                    missing_goal_pairs.add((campaign_id, goal_id))

        return MissingRanges(
            direct_campaign_ids=missing_direct,
            metrika_campaign_ids=missing_metrika,
            metrika_goal_pairs=missing_goal_pairs,
        )

    def combine(
        self,
        campaign_ids: list[int],
        goals: list[Goal],
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> list[ReportDailyRowIn]:
        """Объединяет Direct (показы/клики/расход) и Metrika (достижения
        выбранных целей) в одну строку на кампанию и день.

        На каждую дату периода – ровно одна строка на кампанию, даже без
        исходных данных, иначе временной ряд отчёта содержал бы разрывы.
        conversions/leads – None, если цели не выбраны («не считали», а не
        ноль). visits сюда не входят: CR = conversions / clicks.
        """
        direct_map = {
            (row.campaign_id, row.stat_date): row
            for row in self._statistics.get_direct_range(
                campaign_ids, date_from, date_to
            )
        }

        conversion_goal_ids = {g.id for g in goals if g.is_conversion}
        lead_goal_ids = {g.id for g in goals if g.is_lead}
        conversions_map: dict[tuple[int, datetime.date], int] = defaultdict(
            int
        )
        leads_map: dict[tuple[int, datetime.date], int] = defaultdict(int)
        for row in self._statistics.get_metrika_goal_range(
            campaign_ids, [g.id for g in goals], date_from, date_to
        ):
            key = (row.campaign_id, row.stat_date)
            if row.goal_id in conversion_goal_ids:
                conversions_map[key] += row.goal_reaches
            if row.goal_id in lead_goal_ids:
                leads_map[key] += row.goal_reaches

        rows: list[ReportDailyRowIn] = []
        for campaign_id in campaign_ids:
            for stat_date in sorted(_all_dates(date_from, date_to)):
                key = (campaign_id, stat_date)
                direct = direct_map.get(key)
                rows.append(
                    ReportDailyRowIn(
                        campaign_id=campaign_id,
                        stat_date=stat_date,
                        impressions=direct.impressions if direct else 0,
                        clicks=direct.clicks if direct else 0,
                        cost=float(direct.cost) if direct else 0.0,
                        conversions=(
                            conversions_map.get(key, 0) if goals else None
                        ),
                        leads=leads_map.get(key, 0) if goals else None,
                    )
                )
        return rows
