from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.clients.yandex_direct_client import YandexDirectClient
from app.clients.yandex_metrika_client import YandexMetrikaClient
from app.config import Settings, get_settings
from app.core.exceptions import ForbiddenError
from app.core.security import verify_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.statistics_repository import StatisticsRepository
from app.repositories.user_repository import UserRepository
from app.services.import_service import ImportService
from app.services.report_service import ReportService
from app.services.statistics_service import StatisticsService

DbSession = Annotated[Session, Depends(get_db)]
_admin_security = HTTPBasic()


def get_campaign_repository(db: DbSession) -> CampaignRepository:
    return CampaignRepository(db)


def get_goal_repository(db: DbSession) -> GoalRepository:
    return GoalRepository(db)


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_statistics_repository(db: DbSession) -> StatisticsRepository:
    return StatisticsRepository(db)


def get_report_repository(db: DbSession) -> ReportRepository:
    return ReportRepository(db)


def get_operation_log_repository(db: DbSession) -> OperationLogRepository:
    return OperationLogRepository(db)


def get_statistics_service(
    statistics_repository: Annotated[
        StatisticsRepository, Depends(get_statistics_repository)
    ],
) -> StatisticsService:
    return StatisticsService(statistics_repository)


def get_direct_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> YandexDirectClient:
    return YandexDirectClient(
        token=settings.direct_token(),
        client_login=settings.direct_client_login or None,
    )


def get_metrika_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> YandexMetrikaClient:
    return YandexMetrikaClient(token=settings.metrika_token())


def get_import_service(
    db: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    direct_client: Annotated[YandexDirectClient, Depends(get_direct_client)],
    metrika_client: Annotated[
        YandexMetrikaClient, Depends(get_metrika_client)
    ],
    campaign_repository: Annotated[
        CampaignRepository, Depends(get_campaign_repository)
    ],
    goal_repository: Annotated[GoalRepository, Depends(get_goal_repository)],
    statistics_repository: Annotated[
        StatisticsRepository, Depends(get_statistics_repository)
    ],
    operation_log_repository: Annotated[
        OperationLogRepository, Depends(get_operation_log_repository)
    ],
) -> ImportService:
    return ImportService(
        db=db,
        direct_client=direct_client,
        metrika_client=metrika_client,
        campaign_repository=campaign_repository,
        goal_repository=goal_repository,
        statistics_repository=statistics_repository,
        operation_log_repository=operation_log_repository,
        metrika_counter_id=settings.metrika_counter_id,
        metrika_attribution=settings.metrika_attribution,
    )


def get_report_service(
    db: DbSession,
    report_repository: Annotated[
        ReportRepository, Depends(get_report_repository)
    ],
    campaign_repository: Annotated[
        CampaignRepository, Depends(get_campaign_repository)
    ],
    goal_repository: Annotated[GoalRepository, Depends(get_goal_repository)],
    statistics_service: Annotated[
        StatisticsService, Depends(get_statistics_service)
    ],
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> ReportService:
    return ReportService(
        db=db,
        report_repository=report_repository,
        campaign_repository=campaign_repository,
        goal_repository=goal_repository,
        statistics_service=statistics_service,
        import_service=import_service,
    )


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(_admin_security)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Проверяет Basic-креды и возвращает объект User (нужен для проверки
    роли)."""
    user = users.get_by_username(credentials.username)
    if user is None or not verify_password(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="Ad Reporting"'},
        )
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Пропускает только пользователей с ролью admin.

    Верные креды без роли admin – 403 (ForbiddenError), а не 401: UI в этом
    случае скрывает раздел, а не просит войти заново."""
    if user.role != "admin":
        raise ForbiddenError("Требуются права администратора.")
    return user
