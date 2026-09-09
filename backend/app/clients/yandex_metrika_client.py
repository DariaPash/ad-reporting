"""Клиент API Яндекс Метрики.

Авторизация схемой "OAuth", а не "Bearer" – в отличие от Директа.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import requests

from app.core.exceptions import ExternalApiError

logger = logging.getLogger(__name__)

METRIKA_MANAGEMENT_BASE = "https://api-metrika.yandex.net/management/v1"
METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"


@dataclass(frozen=True)
class MetrikaCounter:
    id: int
    name: str


@dataclass(frozen=True)
class MetrikaGoal:
    id: int
    name: str
    goal_type: str | None


@dataclass(frozen=True)
class MetrikaDailyRow:
    stat_date: date
    campaign_id: int | None
    visits: int
    goal_reaches: dict[int, int]


def normalize_direct_id(value: object) -> str | None:
    """Снять префикс "N-" у идентификатора кампании Метрики.

    Reporting API возвращает CampaignId Директа в direct_id в виде
    "N-<CampaignId>"; поле id – внутреннее значение Метрики, для
    сопоставления кампаний не используется.
    """
    if value in (None, "", "(not set)"):
        return None
    normalized = str(value).strip()
    if normalized.startswith("N-") and normalized[2:].isdigit():
        normalized = normalized[2:]
    return normalized or None


class YandexMetrikaClient:
    def __init__(
        self, token: str, session: requests.Session | None = None
    ) -> None:
        self._token = token
        self._session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"OAuth {self._token}"}

    def get_counters(self) -> list[MetrikaCounter]:
        try:
            response = self._session.get(
                f"{METRIKA_MANAGEMENT_BASE}/counters",
                headers=self._headers(),
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.error("Metrika counters connection error: %s", exc)
            raise ExternalApiError("Яндекс.Метрика недоступна.") from exc
        if not response.ok:
            logger.error(
                "Metrika counters HTTP %s: %s",
                response.status_code,
                response.text[:4000],
            )
            raise ExternalApiError(
                "Не удалось получить список счётчиков Метрики."
            )
        return [
            MetrikaCounter(id=c["id"], name=c["name"])
            for c in response.json().get("counters", [])
        ]

    def get_goals(self, counter_id: str) -> list[MetrikaGoal]:
        try:
            response = self._session.get(
                f"{METRIKA_MANAGEMENT_BASE}/counter/{counter_id}/goals",
                headers=self._headers(),
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.error("Metrika goals connection error: %s", exc)
            raise ExternalApiError("Яндекс.Метрика недоступна.") from exc
        if not response.ok:
            logger.error(
                "Metrika goals HTTP %s: %s",
                response.status_code,
                response.text[:4000],
            )
            raise ExternalApiError("Не удалось получить список целей Метрики.")
        return [
            MetrikaGoal(id=g["id"], name=g["name"], goal_type=g.get("type"))
            for g in response.json().get("goals", [])
        ]

    def get_daily_statistics(
        self,
        counter_id: str,
        goal_ids: list[int],
        date_from: date,
        date_to: date,
        attribution: str = "automatic",
    ) -> list[MetrikaDailyRow]:
        """Визиты и достижения целей по кампании и дню (stat/v1/data).

        accuracy не задаётся (дефолт API): высокую точность на неполном периоде
        запрашивать нельзя, выбор завершённого периода – на вызывающей стороне.
        """
        if date_from > date_to:
            raise ExternalApiError(
                "Некорректный период: дата начала позже даты окончания."
            )

        goal_metrics = ",".join(
            f"ym:s:goal{goal_id}reaches" for goal_id in goal_ids
        )
        metrics = "ym:s:visits" + (f",{goal_metrics}" if goal_metrics else "")
        params = {
            "ids": counter_id,
            "date1": date_from.isoformat(),
            "date2": date_to.isoformat(),
            "dimensions": f"ym:s:date,ym:s:{attribution}DirectClickOrder",
            "metrics": metrics,
            "limit": 100000,
            "lang": "ru",
        }
        try:
            response = self._session.get(
                METRIKA_STAT_URL,
                headers=self._headers(),
                params=params,
                timeout=60,
            )
        except requests.RequestException as exc:
            logger.error("Metrika stat connection error: %s", exc)
            raise ExternalApiError("Яндекс.Метрика недоступна.") from exc
        if not response.ok:
            logger.error(
                "Metrika stat HTTP %s: %s",
                response.status_code,
                response.text[:4000],
            )
            raise ExternalApiError("Не удалось получить статистику Метрики.")

        payload = response.json()
        if payload.get("sampled"):
            logger.info(
                "Metrika response is sampled: sample_share=%s data_lag=%s",
                payload.get("sample_share"),
                payload.get("data_lag"),
            )

        rows: list[MetrikaDailyRow] = []
        for entry in payload.get("data", []):
            dims = entry["dimensions"]
            stat_date = date.fromisoformat(
                dims[0]["name"] if isinstance(dims[0], dict) else dims[0]
            )
            campaign_dim = dims[1]
            raw_id = (
                campaign_dim.get("direct_id")
                if isinstance(campaign_dim, dict)
                else campaign_dim
            )
            campaign_id_str = normalize_direct_id(raw_id)
            values = entry["metrics"]
            visits = int(values[0])
            reaches = {
                goal_id: int(values[i + 1])
                for i, goal_id in enumerate(goal_ids)
            }
            rows.append(
                MetrikaDailyRow(
                    stat_date=stat_date,
                    campaign_id=(
                        int(campaign_id_str) if campaign_id_str else None
                    ),
                    visits=visits,
                    goal_reaches=reaches,
                )
            )
        return rows
