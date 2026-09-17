"""Расчёт производных показателей эффективности.

- сначала суммируются абсолютные показатели за период, только потом вычисляются
относительные – нельзя усреднять готовые дневные CTR/CPC; - при нулевом
знаменателе показатель "не вычисляется" (None), а не 0; - conversions/leads
суммируются из достижений выбранных целей с признаками is_conversion/is_lead;
CPA и CPL – разные показатели, даже если численно совпадают.
"""

from __future__ import annotations

from app.schemas.report import KpiSet


def _safe_ratio(
    numerator: float | None, denominator: float | None
) -> float | None:
    if numerator is None or not denominator:
        return None
    return numerator / denominator


def calculate_kpi(
    impressions: int,
    clicks: int,
    cost: float,
    conversions: int | None,
    leads: int | None,
) -> KpiSet:
    ctr = _safe_ratio(clicks, impressions)
    cpc = _safe_ratio(cost, clicks)
    cr = _safe_ratio(conversions, clicks)
    cpa = _safe_ratio(cost, conversions)
    cpl = _safe_ratio(cost, leads)
    return KpiSet(
        impressions=impressions,
        clicks=clicks,
        cost=cost,
        conversions=conversions,
        leads=leads,
        ctr=ctr * 100 if ctr is not None else None,
        cpc=cpc,
        cr=cr * 100 if cr is not None else None,
        cpa=cpa,
        cpl=cpl,
    )
