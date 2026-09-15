"""Юнит-тесты ImportService: реальная БД (откатываемая транзакция), фейковые
клиенты Direct/Metrika."""

from __future__ import annotations

import datetime

import pytest

from app.clients.yandex_direct_client import DirectCampaign, DirectDailyRow
from app.clients.yandex_metrika_client import MetrikaDailyRow, MetrikaGoal
from app.core.exceptions import ExternalApiError, ValidationDomainError
from app.models.statistics import DirectDailyStatistic
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.statistics_repository import StatisticsRepository
from app.services.import_service import ImportService
from app.services.statistics_service import MissingRanges


class FakeDirectClient:
    def __init__(
        self,
        campaigns=None,
        daily_rows=None,
        error=None,
        discovered_names=None,
        active_ids=None,
    ):
        self._campaigns = campaigns or []
        self._daily_rows = daily_rows or []
        self._error = error
        self._discovered_names = discovered_names or {}
        self._active_ids = active_ids or set()
        self.daily_calls: list[tuple] = []

    def get_campaigns(self):
        if self._error:
            raise self._error
        return self._campaigns

    def get_campaign_names_from_report(self, date_from, date_to):
        """Кампании Мастера (campaigns.get их не видит). По умолчанию пусто."""
        if self._error:
            raise self._error
        return self._discovered_names

    def get_active_campaign_ids(self, date_from, date_to):
        """Эвристика «вероятно активна» по показам – по умолчанию никто не
        активен."""
        if self._error:
            raise self._error
        return self._active_ids

    def get_daily_statistics(
        self, date_from, date_to, direct_campaign_ids=None
    ):
        self.daily_calls.append((date_from, date_to, direct_campaign_ids))
        if self._error:
            raise self._error
        return self._daily_rows


class FakeMetrikaClient:
    def __init__(self, goals=None, daily_rows=None, error=None):
        self._goals = goals or []
        self._daily_rows = daily_rows or []
        self._error = error

    def get_goals(self, counter_id):
        if self._error:
            raise self._error
        return self._goals

    def get_daily_statistics(
        self, counter_id, goal_ids, date_from, date_to, attribution="automatic"
    ):
        if self._error:
            raise self._error
        return self._daily_rows


@pytest.fixture
def repos(db_session):
    return {
        "campaigns": CampaignRepository(db_session),
        "goals": GoalRepository(db_session),
        "statistics": StatisticsRepository(db_session),
        "operation_logs": OperationLogRepository(db_session),
    }


def make_service(db_session, repos, direct_client=None, metrika_client=None):
    return ImportService(
        db=db_session,
        direct_client=direct_client or FakeDirectClient(),
        metrika_client=metrika_client or FakeMetrikaClient(),
        campaign_repository=repos["campaigns"],
        goal_repository=repos["goals"],
        statistics_repository=repos["statistics"],
        operation_log_repository=repos["operation_logs"],
        metrika_counter_id="55327960",
    )


# --------------------------------------------------------------------- #
# sync_campaigns
# --------------------------------------------------------------------- #


def test_sync_campaigns_creates_new_rows(db_session, repos):
    direct = FakeDirectClient(
        campaigns=[
            DirectCampaign(
                id=111, name="Кампания 1", state="ON", status="ACCEPTED"
            )
        ]
    )
    service = make_service(db_session, repos, direct_client=direct)

    result = service.sync_campaigns()

    assert result.created == 1
    assert result.updated == 0
    campaign = repos["campaigns"].get_by_direct_id(111)
    assert campaign is not None
    assert campaign.name == "Кампания 1"
    logs = repos["operation_logs"].list()
    assert logs[0].status == "success"
    assert logs[0].operation_type == "campaigns_sync"


def test_sync_campaigns_discovers_campaign_wizard_campaigns(db_session, repos):
    """Кампании Мастера, которых нет в campaigns.get, донаходятся через отчёт
    статистики; state – эвристика LIKELY_ACTIVE/LIKELY_INACTIVE по показам."""
    direct = FakeDirectClient(
        campaigns=[
            DirectCampaign(
                id=111, name="Обычная кампания", state="ON", status="ACCEPTED"
            )
        ],
        discovered_names={
            111: "Обычная кампания (из отчёта)",
            222: "yd_mk_armatur_karkasy",
            333: "yd_mk_zavod",
        },
        active_ids={222},
    )
    service = make_service(db_session, repos, direct_client=direct)

    result = service.sync_campaigns()

    assert (
        result.created == 3
    )  # 111 из campaigns.get + 222/333 донайдены через отчёт
    assert (
        result.updated == 0
    )  # 111 в отчёте – дубликат уже известного id, не второй upsert
    discovered = repos["campaigns"].get_by_direct_id(222)
    assert discovered is not None
    assert discovered.name == "yd_mk_armatur_karkasy"
    assert discovered.state == "LIKELY_ACTIVE"
    assert discovered.status is None
    inactive = repos["campaigns"].get_by_direct_id(333)
    assert inactive.state == "LIKELY_INACTIVE"
    # 111 обновилось из campaigns.get (реальные state/status), а не из
    # отчёта (там их нет) – имя из отчёта для уже известного id игнорируется.
    known = repos["campaigns"].get_by_direct_id(111)
    assert known.name == "Обычная кампания"
    assert known.state == "ON"


def test_sync_campaigns_empty_response(db_session, repos):
    service = make_service(
        db_session, repos, direct_client=FakeDirectClient(campaigns=[])
    )

    result = service.sync_campaigns()

    assert result.created == 0
    assert result.updated == 0


def test_sync_campaigns_is_idempotent(db_session, repos):
    direct = FakeDirectClient(
        campaigns=[
            DirectCampaign(
                id=111, name="Кампания 1", state="ON", status="ACCEPTED"
            )
        ]
    )
    service = make_service(db_session, repos, direct_client=direct)

    first = service.sync_campaigns()
    second = service.sync_campaigns()

    assert first.created == 1
    assert second.created == 0
    assert second.updated == 1


def test_sync_campaigns_external_api_error_logged_and_raised(
    db_session, repos
):
    direct = FakeDirectClient(
        error=ExternalApiError("Яндекс.Директ недоступен.")
    )
    service = make_service(db_session, repos, direct_client=direct)

    with pytest.raises(ExternalApiError):
        service.sync_campaigns()

    logs = repos["operation_logs"].list()
    assert logs[0].status == "error"
    assert repos["campaigns"].get_by_direct_id(111) is None


def test_sync_campaigns_unexpected_error_still_closes_log(db_session, repos):
    """Любое исключение, не только ExternalApiError, закрывает запись
    журнала."""
    direct = FakeDirectClient(
        error=RuntimeError("нежданчик, не ExternalApiError")
    )
    service = make_service(db_session, repos, direct_client=direct)

    with pytest.raises(RuntimeError):
        service.sync_campaigns()

    logs = repos["operation_logs"].list()
    assert logs[0].status == "error"
    assert logs[0].finished_at is not None
    assert "нежданчик" not in (
        logs[0].message or ""
    )  # str(exc) не должен утекать как есть


# --------------------------------------------------------------------- #
# sync_goals
# --------------------------------------------------------------------- #


def test_sync_goals_creates_new_rows(db_session, repos):
    metrika = FakeMetrikaClient(
        goals=[MetrikaGoal(id=222, name="Заявка", goal_type="url")]
    )
    service = make_service(db_session, repos, metrika_client=metrika)

    result = service.sync_goals()

    assert result.created == 1
    goal = repos["goals"].get_by_metrika_id(55327960, 222)
    assert goal is not None
    assert (
        goal.is_conversion is False
    )  # классификация задаётся отдельно, PATCH /goals/{id}


def test_sync_goals_external_api_error(db_session, repos):
    metrika = FakeMetrikaClient(
        error=ExternalApiError("Яндекс.Метрика недоступна.")
    )
    service = make_service(db_session, repos, metrika_client=metrika)

    with pytest.raises(ExternalApiError):
        service.sync_goals()

    assert repos["operation_logs"].list()[0].status == "error"


def test_sync_goals_is_idempotent(db_session, repos):
    """Повторная синхронизация целей не создаёт дубликатов."""
    metrika = FakeMetrikaClient(
        goals=[MetrikaGoal(id=222, name="Заявка", goal_type="url")]
    )
    service = make_service(db_session, repos, metrika_client=metrika)

    first = service.sync_goals()
    second = service.sync_goals()

    assert first.created == 1
    assert second.created == 0
    assert second.updated == 1


# --------------------------------------------------------------------- #
# fetch_missing
# --------------------------------------------------------------------- #


def test_fetch_missing_rejects_invalid_period(db_session, repos):
    service = make_service(db_session, repos)
    missing = MissingRanges(
        direct_campaign_ids={1},
        metrika_campaign_ids=set(),
        metrika_goal_pairs=set(),
    )

    with pytest.raises(ValidationDomainError):
        service.fetch_missing(
            missing, datetime.date(2026, 1, 10), datetime.date(2026, 1, 1)
        )


def test_fetch_missing_direct_saves_only_requested_campaigns(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    direct = FakeDirectClient(
        daily_rows=[
            DirectDailyRow(
                stat_date=datetime.date(2026, 1, 1),
                campaign_id=111,
                impressions=100,
                clicks=10,
                cost=50.0,
            ),
            DirectDailyRow(
                stat_date=datetime.date(2026, 1, 1),
                campaign_id=999,
                impressions=5,
                clicks=1,
                cost=1.0,
            ),
        ]
    )
    service = make_service(db_session, repos, direct_client=direct)
    missing = MissingRanges(
        direct_campaign_ids={campaign.id},
        metrika_campaign_ids=set(),
        metrika_goal_pairs=set(),
    )

    service.fetch_missing(
        missing, datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)
    )

    dates = repos["statistics"].existing_direct_dates(
        campaign.id, datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)
    )
    assert dates == {datetime.date(2026, 1, 1)}
    assert direct.daily_calls[0][2] == [111]


def test_fetch_missing_direct_error_does_not_save_partial_data(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    direct = FakeDirectClient(
        error=ExternalApiError("Яндекс.Директ недоступен.")
    )
    service = make_service(db_session, repos, direct_client=direct)
    missing = MissingRanges(
        direct_campaign_ids={campaign.id},
        metrika_campaign_ids=set(),
        metrika_goal_pairs=set(),
    )

    with pytest.raises(ExternalApiError):
        service.fetch_missing(
            missing, datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)
        )

    dates = repos["statistics"].existing_direct_dates(
        campaign.id, datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)
    )
    assert dates == set()
    logs = [
        log
        for log in repos["operation_logs"].list()
        if log.source == "direct"
    ]
    assert logs[0].status == "error"


def test_fetch_missing_direct_unexpected_error_still_closes_log(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    direct = FakeDirectClient(
        error=KeyError("value")
    )  # форма реальной ошибки API
    service = make_service(db_session, repos, direct_client=direct)
    missing = MissingRanges(
        direct_campaign_ids={campaign.id},
        metrika_campaign_ids=set(),
        metrika_goal_pairs=set(),
    )

    with pytest.raises(KeyError):
        service.fetch_missing(
            missing, datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)
        )

    logs = [
        log
        for log in repos["operation_logs"].list()
        if log.source == "direct"
    ]
    assert logs[0].status == "error"
    assert logs[0].finished_at is not None


def test_fetch_missing_metrika_saves_visits_and_goal_reaches(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    goal, _ = repos["goals"].upsert_from_metrika(
        55327960, 222, "Заявка", "url"
    )
    db_session.flush()
    metrika = FakeMetrikaClient(
        daily_rows=[
            MetrikaDailyRow(
                stat_date=datetime.date(2026, 1, 1),
                campaign_id=111,
                visits=42,
                goal_reaches={222: 3},
            )
        ]
    )
    service = make_service(db_session, repos, metrika_client=metrika)
    missing = MissingRanges(
        direct_campaign_ids=set(),
        metrika_campaign_ids={campaign.id},
        metrika_goal_pairs={(campaign.id, goal.id)},
    )

    service.fetch_missing(
        missing, datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)
    )

    visit_dates = repos["statistics"].existing_metrika_dates(
        campaign.id, datetime.date(2026, 1, 1), datetime.date(2026, 1, 1)
    )
    goal_dates = repos["statistics"].existing_metrika_goal_dates(
        campaign.id,
        goal.id,
        datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 1),
    )
    assert visit_dates == {datetime.date(2026, 1, 1)}
    assert goal_dates == {datetime.date(2026, 1, 1)}


D1, D2, D3 = (
    datetime.date(2026, 1, 1),
    datetime.date(2026, 1, 2),
    datetime.date(2026, 1, 3),
)


def test_fetch_missing_direct_zero_fills_days_the_api_omits(db_session, repos):
    """Дни без показов, которые Директ не возвращает, заполняются нулём
    и не запрашиваются повторно."""
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    # Реальный Директ прислал бы строку только за D2 – D1 и D3 без показов.
    direct = FakeDirectClient(
        daily_rows=[
            DirectDailyRow(
                stat_date=D2,
                campaign_id=111,
                impressions=100,
                clicks=10,
                cost=50.0,
            )
        ]
    )
    service = make_service(db_session, repos, direct_client=direct)
    missing = MissingRanges(
        direct_campaign_ids={campaign.id},
        metrika_campaign_ids=set(),
        metrika_goal_pairs=set(),
    )

    service.fetch_missing(missing, D1, D3)

    dates = repos["statistics"].existing_direct_dates(campaign.id, D1, D3)
    assert dates == {
        D1,
        D2,
        D3,
    }  # все три дня теперь "подтверждены", не только D2
    for zero_day in (D1, D3):
        row = db_session.get(DirectDailyStatistic, (campaign.id, zero_day))
        assert (
            row.impressions == 0 and row.clicks == 0 and float(row.cost) == 0.0
        )


def test_fetch_missing_metrika_zero_fills_visits_and_goal_reaches(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    goal, _ = repos["goals"].upsert_from_metrika(
        55327960, 222, "Заявка", "url"
    )
    db_session.flush()
    metrika = FakeMetrikaClient(
        daily_rows=[
            MetrikaDailyRow(
                stat_date=D2, campaign_id=111, visits=42, goal_reaches={222: 3}
            )
        ]
    )
    service = make_service(db_session, repos, metrika_client=metrika)
    missing = MissingRanges(
        direct_campaign_ids=set(),
        metrika_campaign_ids={campaign.id},
        metrika_goal_pairs={(campaign.id, goal.id)},
    )

    service.fetch_missing(missing, D1, D3)

    visit_dates = repos["statistics"].existing_metrika_dates(
        campaign.id, D1, D3
    )
    goal_dates = repos["statistics"].existing_metrika_goal_dates(
        campaign.id, goal.id, D1, D3
    )
    assert visit_dates == {D1, D2, D3}
    assert goal_dates == {D1, D2, D3}


# --------------------------------------------------------------------- #
# Атомарность записи партии: сбой в середине партии не должен
# оставлять частично сохранённые данные.
# --------------------------------------------------------------------- #


def test_fetch_missing_direct_mid_batch_failure_leaves_no_partial_data(
    db_session, repos, monkeypatch
):
    campaign1, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    campaign2, _ = repos["campaigns"].upsert_from_direct(
        222, "Кампания 2", "ON", "ACCEPTED"
    )
    db_session.flush()
    direct = FakeDirectClient(
        daily_rows=[
            DirectDailyRow(
                stat_date=D1,
                campaign_id=111,
                impressions=100,
                clicks=10,
                cost=50.0,
            ),
            DirectDailyRow(
                stat_date=D1,
                campaign_id=222,
                impressions=200,
                clicks=20,
                cost=75.0,
            ),
        ]
    )
    service = make_service(db_session, repos, direct_client=direct)

    call_count = {"n": 0}
    original_upsert = repos["statistics"].upsert_direct_daily

    def flaky_upsert(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("симулированный сбой в середине партии")
        return original_upsert(*args, **kwargs)

    monkeypatch.setattr(
        repos["statistics"], "upsert_direct_daily", flaky_upsert
    )
    missing = MissingRanges(
        direct_campaign_ids={campaign1.id, campaign2.id},
        metrika_campaign_ids=set(),
        metrika_goal_pairs=set(),
    )

    with pytest.raises(RuntimeError):
        service.fetch_missing(missing, D1, D1)

    # Первая строка партии успела вставиться до сбоя второй – вся партия
    # должна откатиться целиком, а не сохраниться частично.
    assert (
        repos["statistics"].existing_direct_dates(campaign1.id, D1, D1)
        == set()
    )
    assert (
        repos["statistics"].existing_direct_dates(campaign2.id, D1, D1)
        == set()
    )
    logs = [
        log
        for log in repos["operation_logs"].list()
        if log.source == "direct"
    ]
    assert logs[0].status == "error"
    assert logs[0].finished_at is not None
