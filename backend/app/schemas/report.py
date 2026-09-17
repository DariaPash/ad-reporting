from __future__ import annotations

import datetime

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ReportCreateIn(BaseModel):
    """POST /reports – тело запроса формирования отчёта."""

    date_from: datetime.date
    date_to: datetime.date
    campaign_ids: list[int] = Field(min_length=1)
    goal_ids: list[int] = Field(default_factory=list)

    @field_validator("date_to")
    @classmethod
    def _check_period(
        cls, date_to: datetime.date, info: ValidationInfo
    ) -> datetime.date:
        date_from = info.data.get("date_from")
        if date_from is not None and date_to < date_from:
            raise ValueError("date_to must not be earlier than date_from")
        return date_to


class KpiSet(BaseModel):
    """Показатели эффективности. None означает «не вычисляется», а не ноль."""

    impressions: int
    clicks: int
    cost: float
    conversions: int | None
    leads: int | None
    ctr: float | None
    cpc: float | None
    cr: float | None
    cpa: float | None
    cpl: float | None


class ReportCampaignRow(BaseModel):
    campaign_id: int
    campaign_name: str
    kpi: KpiSet


class ReportDatePoint(BaseModel):
    stat_date: datetime.date
    impressions: int
    clicks: int
    cost: float
    conversions: int | None
    leads: int | None


class ReportGoalOut(BaseModel):
    goal_id: int
    goal_name: str
    is_conversion: bool
    is_lead: bool


class ReportSummaryOut(BaseModel):
    """Одна строка истории отчётов."""

    id: int
    date_from: datetime.date
    date_to: datetime.date
    created_at: datetime.datetime
    campaign_names: list[str]
    goal_names: list[str]


class ReportDetailOut(BaseModel):
    """Полный снимок отчёта – из таблиц-снимков, без обращения к внешним
    API."""

    id: int
    date_from: datetime.date
    date_to: datetime.date
    created_at: datetime.datetime
    goals: list[ReportGoalOut]
    summary: KpiSet
    by_campaign: list[ReportCampaignRow]
    by_date: list[ReportDatePoint]
