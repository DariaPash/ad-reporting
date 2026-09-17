"""Тесты StatisticsService.combine, KpiCalculator и ReportService.create_report
(реальная БД, фейковые клиенты Direct/Metrika).
"""

from __future__ import annotations

import datetime

import pytest

from app.clients.yandex_direct_client import DirectDailyRow
from app.core.exceptions import ExternalApiError, NotFoundError
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.statistics_repository import StatisticsRepository
from app.schemas.report import ReportCreateIn
from app.services.import_service import ImportService
from app.services.kpi_calculator import calculate_kpi
from app.services.report_service import ReportService
from app.services.statistics_service import StatisticsService
from tests.backend.test_import_service import (
    FakeDirectClient,
    FakeMetrikaClient,
)

D1 = datetime.date(2026, 1, 1)
D2 = datetime.date(2026, 1, 2)


@pytest.fixture
def repos(db_session):
    return {
        "campaigns": CampaignRepository(db_session),
        "goals": GoalRepository(db_session),
        "statistics": StatisticsRepository(db_session),
        "operation_logs": OperationLogRepository(db_session),
        "reports": ReportRepository(db_session),
    }


def make_report_service(
    db_session, repos, direct_client=None, metrika_client=None
):
    import_service = ImportService(
        db=db_session,
        direct_client=direct_client
        or FakeDirectClient(error=ExternalApiError("не должен вызываться")),
        metrika_client=metrika_client
        or FakeMetrikaClient(error=ExternalApiError("не должен вызываться")),
        campaign_repository=repos["campaigns"],
        goal_repository=repos["goals"],
        statistics_repository=repos["statistics"],
        operation_log_repository=repos["operation_logs"],
        metrika_counter_id="55327960",
    )
    statistics_service = StatisticsService(repos["statistics"])
    return ReportService(
        db=db_session,
        report_repository=repos["reports"],
        campaign_repository=repos["campaigns"],
        goal_repository=repos["goals"],
        statistics_service=statistics_service,
        import_service=import_service,
    )


# --------------------------------------------------------------------- #
# KpiCalculator – нулевые знаменатели
# --------------------------------------------------------------------- #


def test_kpi_calculator_none_for_zero_impressions():
    kpi = calculate_kpi(
        impressions=0, clicks=0, cost=0.0, conversions=0, leads=0
    )
    assert kpi.ctr is None
    assert kpi.cpc is None
    assert kpi.cr is None
    assert kpi.cpa is None
    assert kpi.cpl is None


def test_kpi_calculator_none_when_goals_not_selected():
    kpi = calculate_kpi(
        impressions=100, clicks=10, cost=50.0, conversions=None, leads=None
    )
    assert kpi.ctr == pytest.approx(10.0)
    assert kpi.cpc == pytest.approx(5.0)
    assert kpi.cr is None
    assert kpi.cpa is None
    assert kpi.cpl is None


def test_kpi_calculator_normal_case():
    kpi = calculate_kpi(
        impressions=1000, clicks=50, cost=500.0, conversions=5, leads=2
    )
    assert kpi.ctr == pytest.approx(5.0)
    assert kpi.cpc == pytest.approx(10.0)
    assert kpi.cr == pytest.approx(10.0)
    assert kpi.cpa == pytest.approx(100.0)
    assert kpi.cpl == pytest.approx(250.0)


# --------------------------------------------------------------------- #
# StatisticsService.combine – объединение источников, заполнение нулями
# --------------------------------------------------------------------- #


def test_combine_fills_zero_for_days_without_direct_data(db_session, repos):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    repos["statistics"].upsert_direct_daily(
        campaign.id, D1, impressions=100, clicks=10, cost=50.0
    )
    db_session.flush()

    rows = StatisticsService(repos["statistics"]).combine(
        [campaign.id], goals=[], date_from=D1, date_to=D2
    )

    by_date = {r.stat_date: r for r in rows}
    assert by_date[D1].impressions == 100
    assert by_date[D2].impressions == 0
    assert by_date[D2].clicks == 0
    assert by_date[D2].cost == 0.0
    assert (
        by_date[D1].conversions is None
    )  # цели не выбраны – не 0, а «не считали»
    assert by_date[D2].conversions is None


def test_combine_sums_only_selected_goal_types(db_session, repos):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    conversion_goal, _ = repos["goals"].upsert_from_metrika(
        55327960, 201, "Покупка", "url"
    )
    lead_goal, _ = repos["goals"].upsert_from_metrika(
        55327960, 202, "Звонок", "url"
    )
    db_session.flush()
    conversion_goal.is_conversion = True
    lead_goal.is_lead = True
    repos["statistics"].upsert_metrika_goal_daily(
        campaign.id, conversion_goal.id, D1, goal_reaches=3
    )
    repos["statistics"].upsert_metrika_goal_daily(
        campaign.id, lead_goal.id, D1, goal_reaches=7
    )
    db_session.flush()

    rows = StatisticsService(repos["statistics"]).combine(
        [campaign.id],
        goals=[conversion_goal, lead_goal],
        date_from=D1,
        date_to=D1,
    )

    assert rows[0].conversions == 3
    assert rows[0].leads == 7


# --------------------------------------------------------------------- #
# ReportService.create_report – полный сценарий
# --------------------------------------------------------------------- #


def test_create_report_uses_existing_data_without_calling_external_apis(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    repos["statistics"].upsert_direct_daily(
        campaign.id, D1, impressions=1000, clicks=50, cost=500.0
    )
    db_session.flush()
    service = make_report_service(
        db_session, repos
    )  # фейки настроены "упасть", если их вызвать

    result = service.create_report(
        ReportCreateIn(
            date_from=D1, date_to=D1, campaign_ids=[campaign.id], goal_ids=[]
        )
    )

    assert result.summary.impressions == 1000
    assert result.summary.ctr == pytest.approx(5.0)
    assert result.by_campaign[0].campaign_name == "Кампания 1"
    assert len(result.by_date) == 1


def test_create_report_fetches_missing_data_then_saves_snapshot(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    direct = FakeDirectClient(
        daily_rows=[
            DirectDailyRow(
                stat_date=D1,
                campaign_id=111,
                impressions=200,
                clicks=20,
                cost=100.0,
            )
        ]
    )
    service = make_report_service(db_session, repos, direct_client=direct)

    result = service.create_report(
        ReportCreateIn(
            date_from=D1, date_to=D1, campaign_ids=[campaign.id], goal_ids=[]
        )
    )

    assert result.summary.impressions == 200
    assert direct.daily_calls  # реально обратились к (фейковому) Директу
    # снимок сохранён – повторное чтение report тоже видит данные
    assert service.get_report(result.id).summary.impressions == 200


def test_create_report_unknown_campaign_raises_not_found(db_session, repos):
    service = make_report_service(db_session, repos)
    with pytest.raises(NotFoundError):
        service.create_report(
            ReportCreateIn(
                date_from=D1, date_to=D1, campaign_ids=[999999], goal_ids=[]
            )
        )


def test_create_report_unknown_goal_raises_not_found(db_session, repos):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    service = make_report_service(db_session, repos)
    with pytest.raises(NotFoundError):
        service.create_report(
            ReportCreateIn(
                date_from=D1,
                date_to=D1,
                campaign_ids=[campaign.id],
                goal_ids=[999999],
            )
        )


def test_create_report_external_api_error_prevents_report_creation(
    db_session, repos
):
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    direct = FakeDirectClient(
        error=ExternalApiError("Яндекс.Директ недоступен.")
    )
    service = make_report_service(db_session, repos, direct_client=direct)
    reports_before = len(repos["reports"].list_summaries(limit=1000))

    with pytest.raises(ExternalApiError):
        service.create_report(
            ReportCreateIn(
                date_from=D1,
                date_to=D1,
                campaign_ids=[campaign.id],
                goal_ids=[],
            )
        )

    assert len(repos["reports"].list_summaries(limit=1000)) == reports_before


def test_saved_report_is_immutable_after_source_statistics_change(
    db_session, repos
):
    """Сохранённый снимок отчёта не меняется после обновления исходной
    статистики (у report_daily_statistics нет FK на таблицы исходной
    статистики)."""
    campaign, _ = repos["campaigns"].upsert_from_direct(
        111, "Кампания 1", "ON", "ACCEPTED"
    )
    db_session.flush()
    repos["statistics"].upsert_direct_daily(
        campaign.id, D1, impressions=100, clicks=10, cost=50.0
    )
    db_session.flush()
    service = make_report_service(db_session, repos)

    report = service.create_report(
        ReportCreateIn(
            date_from=D1, date_to=D1, campaign_ids=[campaign.id], goal_ids=[]
        )
    )
    assert report.summary.impressions == 100

    # Источник обновился «задним числом» – например, повторный импорт после
    # того, как Директ досчитал показы за тот же день.
    repos["statistics"].upsert_direct_daily(
        campaign.id, D1, impressions=999, clicks=10, cost=50.0
    )
    db_session.flush()

    unchanged = service.get_report(report.id)
    assert unchanged.summary.impressions == 100  # снимок, не пересчитывается

    # Новый отчёт за тот же период – это уже другая сущность с новыми данными.
    fresh = service.create_report(
        ReportCreateIn(
            date_from=D1, date_to=D1, campaign_ids=[campaign.id], goal_ids=[]
        )
    )
    assert fresh.id != report.id
    assert fresh.summary.impressions == 999
