from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_report_service
from app.schemas.report import (
    ReportCreateIn,
    ReportDetailOut,
    ReportSummaryOut,
)
from app.services.report_export import build_pdf, build_xlsx
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportDetailOut)
def create_report(
    payload: ReportCreateIn,
    reports: Annotated[ReportService, Depends(get_report_service)],
) -> ReportDetailOut:
    """Формирует отчёт: проверка полноты данных, получение недостающей
    статистики, расчёт показателей, сохранение снимка (см.
    ReportService.create_report)."""
    return reports.create_report(payload)


@router.get("", response_model=list[ReportSummaryOut])
def list_reports(
    reports: Annotated[ReportService, Depends(get_report_service)],
    limit: Annotated[int, Query(le=200)] = 50,
    offset: int = 0,
) -> list[ReportSummaryOut]:
    """История сформированных отчётов."""
    return reports.list_reports(limit=limit, offset=offset)


@router.get("/{report_id}", response_model=ReportDetailOut)
def get_report(
    report_id: int,
    reports: Annotated[ReportService, Depends(get_report_service)],
) -> ReportDetailOut:
    """Снимок отчёта – читается из БД, без обращения к внешним API."""
    return reports.get_report(report_id)


_EXPORT_MEDIA_TYPES = {
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    "pdf": "application/pdf",
}


@router.get("/{report_id}/export")
def export_report(
    report_id: int,
    format: Literal["pdf", "xlsx"],
    reports: Annotated[ReportService, Depends(get_report_service)],
) -> Response:
    """Экспорт сохранённого отчёта – без пересчёта, только чтение снимка."""
    report = reports.get_report(report_id)
    content = build_xlsx(report) if format == "xlsx" else build_pdf(report)
    filename = f"report_{report_id}.{format}"
    return Response(
        content=content,
        media_type=_EXPORT_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
