"""Тесты экспорта отчёта: build_xlsx/build_pdf и API-эндпоинт поверх
сохранённого отчёта."""

from __future__ import annotations

import datetime
import io

import openpyxl
import pytest

from app.clients.yandex_direct_client import DirectDailyRow
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.statistics_repository import StatisticsRepository
from app.schemas.report import (
    KpiSet,
    ReportCampaignRow,
    ReportCreateIn,
    ReportDatePoint,
    ReportDetailOut,
    ReportGoalOut,
)
from app.services.import_service import ImportService
from app.services.report_export import build_pdf, build_xlsx
from app.services.report_service import ReportService
from app.services.statistics_service import StatisticsService
from tests.backend.test_import_service import (
    FakeDirectClient,
    FakeMetrikaClient,
)

D1 = datetime.date(2026, 1, 1)


def _sample_report() -> ReportDetailOut:
    kpi = KpiSet(
        impressions=1000,
        clicks=50,
        cost=500.0,
        conversions=5,
        leads=2,
        ctr=5.0,
        cpc=10.0,
        cr=10.0,
        cpa=100.0,
        cpl=250.0,
    )
    return ReportDetailOut(
        id=1,
        date_from=D1,
        date_to=D1,
        created_at=datetime.datetime(
            2026, 1, 2, 12, 0, tzinfo=datetime.timezone.utc
        ),
        goals=[
            ReportGoalOut(
                goal_id=1,
                goal_name="Покупка",
                is_conversion=True,
                is_lead=False,
            )
        ],
        summary=kpi,
        by_campaign=[
            ReportCampaignRow(
                campaign_id=1, campaign_name="Кампания «Тест»", kpi=kpi
            )
        ],
        by_date=[
            ReportDatePoint(
                stat_date=D1,
                impressions=1000,
                clicks=50,
                cost=500.0,
                conversions=5,
                leads=2,
            )
        ],
    )


def test_build_xlsx_roundtrip_contains_real_values():
    content = build_xlsx(_sample_report())
    assert content[:2] == b"PK"  # xlsx – zip-контейнер

    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active
    all_values = [cell.value for row in ws.iter_rows() for cell in row]
    assert "Кампания «Тест»" in all_values
    assert "Покупка" in " ".join(str(v) for v in all_values if v)
    assert 1000 in all_values  # impressions
    assert 500.0 in all_values  # cost


def test_build_pdf_produces_valid_pdf_bytes():
    content = build_pdf(_sample_report())
    assert content[:4] == b"%PDF"
    assert len(content) > 1000


# --------------------------------------------------------------------- #
# Экспорт через API поверх реально сохранённого отчёта
# --------------------------------------------------------------------- #


@pytest.fixture
def repos(db_session):
    return {
        "campaigns": CampaignRepository(db_session),
        "goals": GoalRepository(db_session),
        "statistics": StatisticsRepository(db_session),
        "operation_logs": OperationLogRepository(db_session),
        "reports": ReportRepository(db_session),
    }


def _seed_report(db_session, repos) -> int:
    campaign, _ = repos["campaigns"].upsert_from_direct(
        222333, "Кампания экспорта", "ON", "ACCEPTED"
    )
    db_session.flush()
    direct = FakeDirectClient(
        daily_rows=[
            DirectDailyRow(
                stat_date=D1,
                campaign_id=222333,
                impressions=100,
                clicks=10,
                cost=50.0,
            )
        ]
    )
    service = ReportService(
        db=db_session,
        report_repository=repos["reports"],
        campaign_repository=repos["campaigns"],
        goal_repository=repos["goals"],
        statistics_service=StatisticsService(repos["statistics"]),
        import_service=ImportService(
            db=db_session,
            direct_client=direct,
            metrika_client=FakeMetrikaClient(),
            campaign_repository=repos["campaigns"],
            goal_repository=repos["goals"],
            statistics_repository=repos["statistics"],
            operation_log_repository=repos["operation_logs"],
            metrika_counter_id="55327960",
        ),
    )
    report = service.create_report(
        ReportCreateIn(
            date_from=D1, date_to=D1, campaign_ids=[campaign.id], goal_ids=[]
        )
    )
    return report.id


def test_export_xlsx_endpoint(client, db_session, repos):
    report_id = _seed_report(db_session, repos)

    response = client.get(
        f"/reports/{report_id}/export", params={"format": "xlsx"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )
    assert response.content[:2] == b"PK"


def test_export_pdf_endpoint(client, db_session, repos):
    report_id = _seed_report(db_session, repos)

    response = client.get(
        f"/reports/{report_id}/export", params={"format": "pdf"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_export_unknown_report_returns_404(client):
    response = client.get(
        "/reports/999999999/export", params={"format": "pdf"}
    )
    assert response.status_code == 404
