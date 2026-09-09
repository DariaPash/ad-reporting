"""Клиент API Яндекс Директа."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import date

import requests

from app.core.exceptions import ExternalApiError

logger = logging.getLogger(__name__)

DIRECT_API_BASE = "https://api.direct.yandex.com/json/v501"
REPORT_POLL_MAX_ATTEMPTS = 20
REPORT_POLL_MIN_DELAY = 1
REPORT_POLL_MAX_DELAY = 60


@dataclass(frozen=True)
class DirectCampaign:
    id: int
    name: str
    state: str | None
    status: str | None


@dataclass(frozen=True)
class DirectDailyRow:
    stat_date: date
    campaign_id: int
    impressions: int
    clicks: int
    cost: float


def _safe_error(response: requests.Response) -> str:
    """Никогда не включает заголовки запроса (в т.ч. Authorization)."""
    try:
        return str(response.json())[:4000]
    except ValueError:
        return response.text[:4000]


class YandexDirectClient:
    def __init__(
        self,
        token: str,
        client_login: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self._token = token
        self._client_login = client_login or None
        self._session = session or requests.Session()

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept-Language": "ru",
            "Content-Type": "application/json; charset=utf-8",
        }
        if self._client_login:
            headers["Client-Login"] = self._client_login
        if extra:
            headers.update(extra)
        return headers

    def get_campaigns(self) -> list[DirectCampaign]:
        """Список кампаний (campaigns.get)."""
        body = {
            "method": "get",
            "params": {
                "SelectionCriteria": {},
                "FieldNames": ["Id", "Name", "State", "Status"],
            },
        }
        try:
            response = self._session.post(
                f"{DIRECT_API_BASE}/campaigns",
                json=body,
                headers=self._headers(),
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.error("Direct campaigns.get connection error: %s", exc)
            raise ExternalApiError("Яндекс.Директ недоступен.") from exc
        data = response.json() if response.ok else None
        # Direct может вернуть ошибку как HTTP 200 с ключом "error" – проверяем
        # явно.
        if data is not None and "error" in data:
            request_id = response.headers.get("RequestId")
            logger.error(
                "Direct campaigns.get error, RequestId=%s: %s",
                request_id,
                data["error"],
            )
            raise ExternalApiError(
                "Не удалось получить список кампаний Директа."
            )
        if not response.ok:
            logger.error(
                "Direct campaigns.get HTTP %s: %s",
                response.status_code,
                _safe_error(response),
            )
            raise ExternalApiError(
                "Не удалось получить список кампаний Директа."
            )
        campaigns = data["result"].get("Campaigns", [])
        return [
            DirectCampaign(
                id=c["Id"],
                name=c["Name"],
                state=c.get("State"),
                status=c.get("Status"),
            )
            for c in campaigns
        ]

    def get_daily_statistics(
        self,
        date_from: date,
        date_to: date,
        direct_campaign_ids: list[int] | None = None,
    ) -> list[DirectDailyRow]:
        """Дневная статистика по кампаниям (CAMPAIGN_PERFORMANCE_REPORT).

        Отчёт асинхронный: 200 – готов, 201/202 – в очереди (ждём retryIn
        секунд и повторяем), другое – ошибка. `direct_campaign_ids` – внешние
        ID Директа; при None отчёт строится по всем кампаниям аккаунта.
        """
        if date_from > date_to:
            raise ExternalApiError(
                "Некорректный период: дата начала позже даты окончания."
            )

        headers = self._headers(
            {
                "processingMode": "auto",
                "returnMoneyInMicros": "false",
                "skipReportHeader": "true",
                "skipReportSummary": "true",
            }
        )
        selection_criteria = {
            "DateFrom": date_from.isoformat(),
            "DateTo": date_to.isoformat(),
        }
        if direct_campaign_ids:
            selection_criteria["Filter"] = [
                {
                    "Field": "CampaignId",
                    "Operator": "IN",
                    "Values": [str(i) for i in direct_campaign_ids],
                }
            ]
        body = {
            "params": {
                "SelectionCriteria": selection_criteria,
                "FieldNames": [
                    "Date",
                    "CampaignId",
                    "Impressions",
                    "Clicks",
                    "Cost",
                ],
                "ReportName": f"ad-reporting_{uuid.uuid4().hex}",
                "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "YES",
            }
        }

        response = None
        for attempt in range(REPORT_POLL_MAX_ATTEMPTS):
            try:
                response = self._session.post(
                    f"{DIRECT_API_BASE}/reports",
                    json=body,
                    headers=headers,
                    timeout=60,
                )
            except requests.RequestException as exc:
                logger.error("Direct reports connection error: %s", exc)
                raise ExternalApiError("Яндекс.Директ недоступен.") from exc
            if response.status_code == 200:
                break
            if response.status_code in (201, 202):
                delay = min(
                    max(
                        int(response.headers.get("retryIn", "5")),
                        REPORT_POLL_MIN_DELAY,
                    ),
                    REPORT_POLL_MAX_DELAY,
                )
                logger.info(
                    "Direct report queued (attempt %s), retry in %ss",
                    attempt + 1,
                    delay,
                )
                time.sleep(delay)
                continue
            logger.error(
                "Direct reports HTTP %s: %s",
                response.status_code,
                _safe_error(response),
            )
            raise ExternalApiError("Не удалось получить статистику Директа.")
        else:
            raise ExternalApiError(
                "Отчёт Директа не был готов вовремя, попробуйте позже."
            )

        return self._parse_tsv(response.text)

    def get_campaign_names_from_report(
        self, date_from: date, date_to: date
    ) -> dict[int, str]:
        """Id и названия кампаний из отчёта за период (одна строка на
        кампанию).

        Нужно для Мастера кампаний: campaigns.get такие кампании не возвращает
        вовсе, а отчётный сервис – отдаёт.
        """
        headers = self._headers(
            {
                "processingMode": "auto",
                "returnMoneyInMicros": "false",
                "skipReportHeader": "true",
                "skipReportSummary": "true",
            }
        )
        body = {
            "params": {
                "SelectionCriteria": {
                    "DateFrom": date_from.isoformat(),
                    "DateTo": date_to.isoformat(),
                },
                "FieldNames": ["CampaignId", "CampaignName"],
                "ReportName": f"ad-reporting-discovery_{uuid.uuid4().hex}",
                "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "YES",
            }
        }

        response = None
        for attempt in range(REPORT_POLL_MAX_ATTEMPTS):
            try:
                response = self._session.post(
                    f"{DIRECT_API_BASE}/reports",
                    json=body,
                    headers=headers,
                    timeout=60,
                )
            except requests.RequestException as exc:
                logger.error(
                    "Direct discovery report connection error: %s", exc
                )
                raise ExternalApiError("Яндекс.Директ недоступен.") from exc
            if response.status_code == 200:
                break
            if response.status_code in (201, 202):
                delay = min(
                    max(
                        int(response.headers.get("retryIn", "5")),
                        REPORT_POLL_MIN_DELAY,
                    ),
                    REPORT_POLL_MAX_DELAY,
                )
                time.sleep(delay)
                continue
            logger.error(
                "Direct discovery report HTTP %s: %s",
                response.status_code,
                _safe_error(response),
            )
            raise ExternalApiError(
                "Не удалось получить список кампаний Директа."
            )
        else:
            raise ExternalApiError(
                "Отчёт Директа не был готов вовремя, попробуйте позже."
            )

        names: dict[int, str] = {}
        for line in response.text.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            try:
                campaign_id = int(parts[0])
            except ValueError:
                continue
            names[campaign_id] = parts[1]
        return names

    def get_active_campaign_ids(
        self, date_from: date, date_to: date
    ) -> set[int]:
        """Кампании с ненулевыми показами за период.

        Эвристика «вероятно активна» для Мастера кампаний, у которых
        campaigns.get не даёт State. Не настоящий статус Директа.
        """
        headers = self._headers(
            {
                "processingMode": "auto",
                "returnMoneyInMicros": "false",
                "skipReportHeader": "true",
                "skipReportSummary": "true",
            }
        )
        body = {
            "params": {
                "SelectionCriteria": {
                    "DateFrom": date_from.isoformat(),
                    "DateTo": date_to.isoformat(),
                },
                "FieldNames": ["CampaignId", "Impressions"],
                "ReportName": f"ad-reporting-activity_{uuid.uuid4().hex}",
                "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "YES",
            }
        }

        response = None
        for attempt in range(REPORT_POLL_MAX_ATTEMPTS):
            try:
                response = self._session.post(
                    f"{DIRECT_API_BASE}/reports",
                    json=body,
                    headers=headers,
                    timeout=60,
                )
            except requests.RequestException as exc:
                logger.error(
                    "Direct activity report connection error: %s", exc
                )
                raise ExternalApiError("Яндекс.Директ недоступен.") from exc
            if response.status_code == 200:
                break
            if response.status_code in (201, 202):
                delay = min(
                    max(
                        int(response.headers.get("retryIn", "5")),
                        REPORT_POLL_MIN_DELAY,
                    ),
                    REPORT_POLL_MAX_DELAY,
                )
                time.sleep(delay)
                continue
            logger.error(
                "Direct activity report HTTP %s: %s",
                response.status_code,
                _safe_error(response),
            )
            raise ExternalApiError(
                "Не удалось получить список кампаний Директа."
            )
        else:
            raise ExternalApiError(
                "Отчёт Директа не был готов вовремя, попробуйте позже."
            )

        active: set[int] = set()
        for line in response.text.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            try:
                campaign_id = int(parts[0])
                impressions = int(parts[1])
            except ValueError:
                continue
            if impressions > 0:
                active.add(campaign_id)
        return active

    @staticmethod
    def _parse_tsv(text: str) -> list[DirectDailyRow]:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            return []
        header = lines[0].split("\t")
        rows = []
        for line in lines[1:]:
            values = dict(zip(header, line.split("\t")))
            rows.append(
                DirectDailyRow(
                    stat_date=date.fromisoformat(values["Date"]),
                    campaign_id=int(values["CampaignId"]),
                    impressions=int(values["Impressions"]),
                    clicks=int(values["Clicks"]),
                    cost=float(values["Cost"]),
                )
            )
        return rows
