"""ORM-модели. Импорт всех модулей здесь нужен, чтобы Base.metadata видела все
таблицы (используется в alembic/env.py и в тестах для create_all)."""

from app.models.campaign import Campaign
from app.models.goal import Goal
from app.models.operation_log import OperationLog
from app.models.report import (
    Report,
    ReportCampaign,
    ReportDailyStatistic,
    ReportGoal,
)
from app.models.statistics import (
    DirectDailyStatistic,
    MetrikaDailyStatistic,
    MetrikaGoalDailyStatistic,
)
from app.models.user import User

__all__ = [
    "Campaign",
    "Goal",
    "OperationLog",
    "Report",
    "ReportCampaign",
    "ReportGoal",
    "ReportDailyStatistic",
    "DirectDailyStatistic",
    "MetrikaDailyStatistic",
    "MetrikaGoalDailyStatistic",
    "User",
]
