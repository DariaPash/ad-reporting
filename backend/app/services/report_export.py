"""Экспорт сохранённого отчёта в PDF/XLSX – только чтение снимка, без пересчёта
KPI и без обращения к внешним API.
"""

from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.report import KpiSet, ReportDetailOut

# Пакет fonts-dejavu-core (см. backend/Dockerfile) – Helvetica у reportlab
# кириллицу не поддерживает.
_DEJAVU_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

_KPI_HEADERS = [
    "Показы",
    "Клики",
    "Расход",
    "Конверсии",
    "Лиды",
    "CTR, %",
    "CPC",
    "CR, %",
    "CPA",
    "CPL",
]


def _fmt(value: float | int | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _kpi_row(kpi: KpiSet) -> list[str]:
    return [
        _fmt(kpi.impressions),
        _fmt(kpi.clicks),
        _fmt(kpi.cost),
        _fmt(kpi.conversions),
        _fmt(kpi.leads),
        _fmt(kpi.ctr),
        _fmt(kpi.cpc),
        _fmt(kpi.cr),
        _fmt(kpi.cpa),
        _fmt(kpi.cpl),
    ]


def _goal_names(report: ReportDetailOut) -> str:
    return ", ".join(g.goal_name for g in report.goals) or "не выбраны"


def build_xlsx(report: ReportDetailOut) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчёт"
    bold = Font(bold=True)

    ws.append(["Отчёт по рекламным кампаниям"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append(
        [
            f"Период: {report.date_from.isoformat()}"
            f" — {report.date_to.isoformat()}"
        ]
    )
    ws.append([f"Сформирован: {report.created_at.isoformat()}"])
    ws.append([f"Цели: {_goal_names(report)}"])
    ws.append([])

    ws.append(["Итоговые показатели"])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.append(_KPI_HEADERS)
    for cell in ws[ws.max_row]:
        cell.font = bold
    ws.append(_kpi_row(report.summary))
    ws.append([])

    ws.append(["По кампаниям"])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.append(["Кампания", *_KPI_HEADERS])
    for cell in ws[ws.max_row]:
        cell.font = bold
    for row in report.by_campaign:
        ws.append([row.campaign_name, *_kpi_row(row.kpi)])
    ws.append([])

    ws.append(["По дням"])
    ws.cell(row=ws.max_row, column=1).font = bold
    ws.append(["Дата", "Показы", "Клики", "Расход", "Конверсии", "Лиды"])
    for cell in ws[ws.max_row]:
        cell.font = bold
    for point in report.by_date:
        ws.append(
            [
                point.stat_date.isoformat(),
                point.impressions,
                point.clicks,
                float(point.cost),
                point.conversions if point.conversions is not None else "—",
                point.leads if point.leads is not None else "—",
            ]
        )

    for column_cells in ws.columns:
        values = [
            str(cell.value) for cell in column_cells if cell.value is not None
        ]
        width = max((len(v) for v in values), default=10)
        ws.column_dimensions[column_cells[0].column_letter].width = min(
            max(width + 2, 10), 40
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def build_pdf(report: ReportDetailOut) -> bytes:
    pdfmetrics.registerFont(TTFont("DejaVuSans", _DEJAVU_REGULAR))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", _DEJAVU_BOLD))

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "normal_ru",
        parent=styles["Normal"],
        fontName="DejaVuSans",
        fontSize=10,
        leading=13,
    )
    heading = ParagraphStyle(
        "heading_ru",
        parent=styles["Heading2"],
        fontName="DejaVuSans-Bold",
        fontSize=13,
        spaceAfter=6,
    )
    title = ParagraphStyle(
        "title_ru",
        parent=styles["Title"],
        fontName="DejaVuSans-Bold",
        fontSize=16,
    )

    table_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm
    )
    story = [
        Paragraph("Отчёт по рекламным кампаниям", title),
        Spacer(1, 6),
        Paragraph(
            f"Период: {report.date_from.isoformat()}"
            f" — {report.date_to.isoformat()}",
            normal,
        ),
        Paragraph(f"Сформирован: {report.created_at.isoformat()}", normal),
        Paragraph(
            "Кампании: "
            + ", ".join(c.campaign_name for c in report.by_campaign),
            normal,
        ),
        Paragraph(f"Цели: {_goal_names(report)}", normal),
        Spacer(1, 10),
        Paragraph("Итоговые показатели", heading),
        Table(
            [_KPI_HEADERS, _kpi_row(report.summary)],
            style=table_style,
            hAlign="LEFT",
        ),
        Spacer(1, 10),
        Paragraph("По кампаниям", heading),
        Table(
            [["Кампания", *_KPI_HEADERS]]
            + [
                [row.campaign_name, *_kpi_row(row.kpi)]
                for row in report.by_campaign
            ],
            style=table_style,
            hAlign="LEFT",
        ),
        Spacer(1, 10),
        Paragraph("По дням", heading),
        Table(
            [["Дата", "Показы", "Клики", "Расход", "Конверсии", "Лиды"]]
            + [
                [
                    point.stat_date.isoformat(),
                    _fmt(point.impressions),
                    _fmt(point.clicks),
                    _fmt(point.cost),
                    _fmt(point.conversions),
                    _fmt(point.leads),
                ]
                for point in report.by_date
            ],
            style=table_style,
            hAlign="LEFT",
        ),
    ]

    doc.build(story)
    return buffer.getvalue()
