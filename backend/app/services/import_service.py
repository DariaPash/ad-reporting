"""Получение и сохранение статистики из Яндекс Директа/Метрики.

Запись идемпотентна (UPSERT по первичному ключу), одна транзакция на партию.
Запись журнала закрывается (success/error) при любом исключении, не только
ExternalApiError – иначе она осталась бы в статусе "running" навсегда.
"""

from __future__ import annotations

import datetime
import logging

from sqlalchemy.orm import Session

from app.clients.yandex_direct_client import YandexDirectClient
from app.clients.yandex_metrika_client import YandexMetrikaClient
from app.core.exceptions import ExternalApiError, ValidationDomainError
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.statistics_repository import StatisticsRepository
from app.schemas.campaign import CampaignSyncResult
from app.schemas.goal import GoalSyncResult
from app.services.statistics_service import MissingRanges

logger = logging.getLogger(__name__)


def _date_range(
    date_from: datetime.date, date_to: datetime.date
) -> list[datetime.date]:
    days = (date_to - date_from).days
    return [date_from + datetime.timedelta(days=i) for i in range(days + 1)]


def _safe_error_message(exc: Exception) -> str:
    """Сообщение для operation_logs.message – никогда не str(exc) для
    непредвиденных исключений: неизвестно, что окажется в тексте."""
    if isinstance(exc, ExternalApiError):
        return str(exc)
    return f"Внутренняя ошибка ({type(exc).__name__})."


class ImportService:
    def __init__(
        self,
        db: Session,
        direct_client: YandexDirectClient,
        metrika_client: YandexMetrikaClient,
        campaign_repository: CampaignRepository,
        goal_repository: GoalRepository,
        statistics_repository: StatisticsRepository,
        operation_log_repository: OperationLogRepository,
        metrika_counter_id: str,
        metrika_attribution: str = "automatic",
    ) -> None:
        self._db = db
        self._direct_client = direct_client
        self._metrika_client = metrika_client
        self._campaigns = campaign_repository
        self._goals = goal_repository
        self._statistics = statistics_repository
        self._operation_logs = operation_log_repository
        self._metrika_counter_id = metrika_counter_id
        self._metrika_attribution = metrika_attribution

    # ------------------------------------------------------------------ #
    # Синхронизация справочников
    # ------------------------------------------------------------------ #

    def sync_campaigns(self) -> CampaignSyncResult:
        """POST /campaigns/sync. Одна транзакция на весь ответ Директа –
        справочник обновляется либо целиком, либо (при ошибке) никак."""
        log = self._operation_logs.start(
            operation_type="campaigns_sync", source="direct"
        )
        # "running" зафиксирован сразу – переживёт откат данных ниже
        self._db.commit()

        try:
            campaigns = self._direct_client.get_campaigns()
            created = updated = 0
            known_ids: set[int] = set()
            for c in campaigns:
                known_ids.add(c.id)
                _, was_created = self._campaigns.upsert_from_direct(
                    direct_campaign_id=c.id,
                    name=c.name,
                    state=c.state,
                    status=c.status,
                )
                created += int(was_created)
                updated += int(not was_created)

            # Мастер кампаний campaigns.get не возвращает, но он виден в отчёте
            # статистики – донаходим такие кампании за последние 90 дней. State
            # Директ для них не отдаёт, поэтому активность оцениваем по показам
            # за 7 дней и пишем отдельные значения
            # LIKELY_ACTIVE/LIKELY_INACTIVE, не пересекающиеся с настоящими
            # State Директа (ON/SUSPENDED/ARCHIVED/...).
            discovery_from = datetime.date.today() - datetime.timedelta(
                days=90
            )
            discovery_to = datetime.date.today()
            discovered = self._direct_client.get_campaign_names_from_report(
                discovery_from, discovery_to
            )
            recent_from = datetime.date.today() - datetime.timedelta(days=7)
            recent_to = datetime.date.today()
            active_ids = (
                self._direct_client.get_active_campaign_ids(
                    recent_from, recent_to
                )
                if discovered
                else set()
            )
            for direct_campaign_id, name in discovered.items():
                if direct_campaign_id in known_ids:
                    continue
                heuristic_state = (
                    "LIKELY_ACTIVE"
                    if direct_campaign_id in active_ids
                    else "LIKELY_INACTIVE"
                )
                _, was_created = self._campaigns.upsert_from_direct(
                    direct_campaign_id=direct_campaign_id,
                    name=name,
                    state=heuristic_state,
                    status=None,
                )
                created += int(was_created)
                updated += int(not was_created)

            self._operation_logs.finish(
                log,
                status="success",
                records_processed=len(campaigns) + len(discovered),
            )
            self._db.commit()
            return CampaignSyncResult(created=created, updated=updated)
        except Exception as exc:
            # Любое исключение, не только ExternalApiError – иначе строка
            # журнала остаётся "running" навсегда при непредвиденной ошибке.
            self._db.rollback()
            self._operation_logs.finish(
                log, status="error", message=_safe_error_message(exc)
            )
            self._db.commit()
            raise

    def sync_goals(self) -> GoalSyncResult:
        """POST /goals/sync. counter_id берётся из конфигурации, не из запроса:
        схема рассчитана на один активный счётчик."""
        log = self._operation_logs.start(
            operation_type="goals_sync", source="metrika"
        )
        self._db.commit()

        try:
            goals = self._metrika_client.get_goals(self._metrika_counter_id)
            created = updated = 0
            for g in goals:
                _, was_created = self._goals.upsert_from_metrika(
                    counter_id=int(self._metrika_counter_id),
                    metrika_goal_id=g.id,
                    name=g.name,
                    goal_type=g.goal_type,
                )
                created += int(was_created)
                updated += int(not was_created)
            self._operation_logs.finish(
                log, status="success", records_processed=len(goals)
            )
            self._db.commit()
            return GoalSyncResult(created=created, updated=updated)
        except Exception as exc:
            self._db.rollback()
            self._operation_logs.finish(
                log, status="error", message=_safe_error_message(exc)
            )
            self._db.commit()
            raise

    # ------------------------------------------------------------------ #
    # Получение недостающей статистики (вызывается из ReportService)
    # ------------------------------------------------------------------ #

    def fetch_missing(
        self,
        missing: MissingRanges,
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> None:
        """Получает у Direct/Metrika только недостающие данные и сохраняет их.

        Один источник – одна транзакция на вызов: сбой одного источника не
        отменяет уже сохранённые данные другого.
        """
        if date_from > date_to:
            raise ValidationDomainError(
                "Некорректный период: дата начала позже даты окончания."
            )

        if missing.direct_campaign_ids:
            self._fetch_direct(
                sorted(missing.direct_campaign_ids), date_from, date_to
            )

        if missing.metrika_campaign_ids or missing.metrika_goal_pairs:
            self._fetch_metrika(
                sorted(missing.metrika_campaign_ids),
                sorted(missing.metrika_goal_pairs),
                date_from,
                date_to,
            )

    def _fetch_direct(
        self,
        campaign_ids: list[int],
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> None:
        campaigns = self._campaigns.get_many(campaign_ids)
        direct_to_internal = {c.direct_campaign_id: c.id for c in campaigns}
        log = self._operation_logs.start(
            operation_type="statistics_import",
            source="direct",
            date_from=date_from,
            date_to=date_to,
        )
        # "running" зафиксирован сразу – переживёт откат данных ниже
        self._db.commit()

        try:
            rows = self._direct_client.get_daily_statistics(
                date_from,
                date_to,
                direct_campaign_ids=list(direct_to_internal.keys()),
            )
            seen: set[tuple[int, datetime.date]] = set()
            saved = 0
            for row in rows:
                internal_id = direct_to_internal.get(row.campaign_id)
                if internal_id is None:
                    continue  # кампания вне запрошенного набора – пропускаем
                self._statistics.upsert_direct_daily(
                    internal_id,
                    row.stat_date,
                    row.impressions,
                    row.clicks,
                    row.cost,
                )
                seen.add((internal_id, row.stat_date))
                saved += 1

            # Директ не возвращает строку за день без показов – без явного нуля
            # find_missing считал бы такой день недостающим и запрашивал бы его
            # снова при каждом формировании отчёта.
            for internal_id in direct_to_internal.values():
                for stat_date in _date_range(date_from, date_to):
                    if (internal_id, stat_date) not in seen:
                        self._statistics.upsert_direct_daily(
                            internal_id, stat_date, 0, 0, 0.0
                        )
                        saved += 1

            self._operation_logs.finish(
                log, status="success", records_processed=saved
            )
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            self._operation_logs.finish(
                log, status="error", message=_safe_error_message(exc)
            )
            self._db.commit()
            raise

    def _fetch_metrika(
        self,
        visit_campaign_ids: list[int],
        goal_pairs: list[tuple[int, int]],
        date_from: datetime.date,
        date_to: datetime.date,
    ) -> None:
        campaign_ids = sorted(
            {*visit_campaign_ids, *(c for c, _ in goal_pairs)}
        )
        campaigns = self._campaigns.get_many(campaign_ids)
        direct_to_internal = {c.direct_campaign_id: c.id for c in campaigns}

        goal_ids_internal = sorted({g for _, g in goal_pairs})
        goals = self._goals.get_many(goal_ids_internal)
        internal_to_external_goal = {g.id: g.metrika_goal_id for g in goals}
        external_to_internal_goal = {
            v: k for k, v in internal_to_external_goal.items()
        }
        external_goal_ids = list(internal_to_external_goal.values())

        log = self._operation_logs.start(
            operation_type="statistics_import",
            source="metrika",
            date_from=date_from,
            date_to=date_to,
        )
        self._db.commit()

        try:
            rows = self._metrika_client.get_daily_statistics(
                counter_id=self._metrika_counter_id,
                goal_ids=external_goal_ids,
                date_from=date_from,
                date_to=date_to,
                attribution=self._metrika_attribution,
            )
            visits_seen: set[tuple[int, datetime.date]] = set()
            goals_seen: set[tuple[int, int, datetime.date]] = set()
            saved = 0
            for row in rows:
                if row.campaign_id is None:
                    continue  # "(not set)"/неопознанная кампания – пропускаем
                internal_campaign_id = direct_to_internal.get(row.campaign_id)
                if internal_campaign_id is None:
                    continue

                if internal_campaign_id in visit_campaign_ids:
                    self._statistics.upsert_metrika_daily(
                        internal_campaign_id, row.stat_date, row.visits
                    )
                    visits_seen.add((internal_campaign_id, row.stat_date))
                    saved += 1

                for external_goal_id, reaches in row.goal_reaches.items():
                    internal_goal_id = external_to_internal_goal.get(
                        external_goal_id
                    )
                    if internal_goal_id is None:
                        continue
                    if (
                        internal_campaign_id,
                        internal_goal_id,
                    ) not in goal_pairs:
                        continue
                    self._statistics.upsert_metrika_goal_daily(
                        internal_campaign_id,
                        internal_goal_id,
                        row.stat_date,
                        reaches,
                    )
                    goals_seen.add(
                        (internal_campaign_id, internal_goal_id, row.stat_date)
                    )
                    saved += 1

            # Metrika тоже не возвращает строку за день без визитов
            # у кампании – без явного нуля find_missing никогда не считал бы
            # такой день полученным.
            date_range = _date_range(date_from, date_to)
            for campaign_id in visit_campaign_ids:
                for stat_date in date_range:
                    if (campaign_id, stat_date) not in visits_seen:
                        self._statistics.upsert_metrika_daily(
                            campaign_id, stat_date, 0
                        )
                        saved += 1
            for campaign_id, goal_id in goal_pairs:
                for stat_date in date_range:
                    if (campaign_id, goal_id, stat_date) not in goals_seen:
                        self._statistics.upsert_metrika_goal_daily(
                            campaign_id, goal_id, stat_date, 0
                        )
                        saved += 1

            self._operation_logs.finish(
                log, status="success", records_processed=saved
            )
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            self._operation_logs.finish(
                log, status="error", message=_safe_error_message(exc)
            )
            self._db.commit()
            raise
