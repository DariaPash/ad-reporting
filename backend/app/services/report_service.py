"""Формирование и чтение отчётов.

Чтение – только из сохранённого снимка, без обращения к внешним API.
Формирование: проверка кампаний/целей → поиск недостающей статистики →
догрузка через ImportService (ошибка внешнего API останавливает сценарий до
сохранения) → объединение источников → сохранение снимка одной транзакцией.
"""

from __future__ import annotations

import datetime
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.report import Report
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.report import (
    KpiSet,
    ReportCampaignRow,
    ReportCreateIn,
    ReportDatePoint,
    ReportDetailOut,
    ReportGoalOut,
    ReportSummaryOut,
)
from app.services.import_service import ImportService
from app.services.kpi_calculator import calculate_kpi
from app.services.statistics_service import StatisticsService


class ReportService:
    def __init__(
        self,
        db: Session,
        report_repository: ReportRepository,
        campaign_repository: CampaignRepository,
        goal_repository: GoalRepository,
        statistics_service: StatisticsService,
        import_service: ImportService,
    ) -> None:
        self._db = db
        self._reports = report_repository
        self._campaigns = campaign_repository
        self._goals = goal_repository
        self._statistics_service = statistics_service
        self._import_service = import_service

    def list_reports(
        self, limit: int = 50, offset: int = 0
    ) -> list[ReportSummaryOut]:
        reports = self._reports.list_summaries(limit=limit, offset=offset)
        return [
            ReportSummaryOut(
                id=r.id,
                date_from=r.date_from,
                date_to=r.date_to,
                created_at=r.created_at,
                campaign_names=[c.campaign_name_snapshot for c in r.campaigns],
                goal_names=[g.goal_name_snapshot for g in r.goals],
            )
            for r in reports
        ]

    def get_report(self, report_id: int) -> ReportDetailOut:
        report = self._reports.get_detail(report_id)
        if report is None:
            raise NotFoundError(f"Отчёт {report_id} не найден.")
        return self._to_detail(report)

    def create_report(self, payload: ReportCreateIn) -> ReportDetailOut:
        """POST /reports. Сценарий описан в докстринге модуля."""
        campaigns = self._campaigns.get_many(payload.campaign_ids)
        found_campaign_ids = {c.id for c in campaigns}
        missing_campaign_ids = set(payload.campaign_ids) - found_campaign_ids
        if missing_campaign_ids:
            raise NotFoundError(
                f"Кампании не найдены: {sorted(missing_campaign_ids)}."
            )

        goals = self._goals.get_many(payload.goal_ids)
        found_goal_ids = {g.id for g in goals}
        missing_goal_ids = set(payload.goal_ids) - found_goal_ids
        if missing_goal_ids:
            raise NotFoundError(
                f"Цели не найдены: {sorted(missing_goal_ids)}."
            )

        missing = self._statistics_service.find_missing(
            campaign_ids=payload.campaign_ids,
            goal_ids=payload.goal_ids,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        if not missing.is_complete:
            self._import_service.fetch_missing(
                missing, payload.date_from, payload.date_to
            )

        daily_rows = self._statistics_service.combine(
            campaign_ids=payload.campaign_ids,
            goals=goals,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )

        report = self._reports.create(
            date_from=payload.date_from,
            date_to=payload.date_to,
            campaigns=[(c.id, c.name) for c in campaigns],
            goals=[(g.id, g.name, g.is_conversion, g.is_lead) for g in goals],
            daily_rows=daily_rows,
        )
        self._db.commit()

        return self.get_report(report.id)

    @staticmethod
    def _to_detail(report: Report) -> ReportDetailOut:
        campaign_names = {
            c.campaign_id: c.campaign_name_snapshot for c in report.campaigns
        }

        by_campaign_totals: dict[int, dict[str, float | int]] = defaultdict(
            lambda: {
                "impressions": 0,
                "clicks": 0,
                "cost": 0.0,
                "conversions": None,
                "leads": None,
            }
        )
        by_date_totals: dict[datetime.date, dict[str, float | int]] = (
            defaultdict(
                lambda: {
                    "impressions": 0,
                    "clicks": 0,
                    "cost": 0.0,
                    "conversions": None,
                    "leads": None,
                }
            )
        )

        def _add(bucket: dict[str, float | int], row) -> None:
            bucket["impressions"] += row.impressions
            bucket["clicks"] += row.clicks
            bucket["cost"] = float(bucket["cost"]) + float(row.cost)
            if row.conversions is not None:
                bucket["conversions"] = (
                    bucket["conversions"] or 0
                ) + row.conversions
            if row.leads is not None:
                bucket["leads"] = (bucket["leads"] or 0) + row.leads

        total_bucket = {
            "impressions": 0,
            "clicks": 0,
            "cost": 0.0,
            "conversions": None,
            "leads": None,
        }
        for row in report.daily_statistics:
            _add(total_bucket, row)
            _add(by_campaign_totals[row.campaign_id], row)
            _add(by_date_totals[row.stat_date], row)

        summary: KpiSet = calculate_kpi(**total_bucket)

        by_campaign = [
            ReportCampaignRow(
                campaign_id=campaign_id,
                campaign_name=campaign_names.get(
                    campaign_id, f"#{campaign_id}"
                ),
                kpi=calculate_kpi(**totals),
            )
            for campaign_id, totals in sorted(by_campaign_totals.items())
        ]

        by_date = [
            ReportDatePoint(stat_date=stat_date, **totals)
            for stat_date, totals in sorted(by_date_totals.items())
        ]

        goals = [
            ReportGoalOut(
                goal_id=g.goal_id,
                goal_name=g.goal_name_snapshot,
                is_conversion=g.is_conversion_snapshot,
                is_lead=g.is_lead_snapshot,
            )
            for g in report.goals
        ]

        return ReportDetailOut(
            id=report.id,
            date_from=report.date_from,
            date_to=report.date_to,
            created_at=report.created_at,
            goals=goals,
            summary=summary,
            by_campaign=by_campaign,
            by_date=by_date,
        )
