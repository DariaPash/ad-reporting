from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_goal_repository, get_import_service
from app.core.exceptions import NotFoundError
from app.repositories.goal_repository import GoalRepository
from app.schemas.goal import GoalClassificationIn, GoalOut, GoalSyncResult
from app.services.import_service import ImportService

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalOut])
def list_goals(
    goals: Annotated[GoalRepository, Depends(get_goal_repository)],
) -> list[GoalOut]:
    """Список целей (с признаками is_conversion/is_lead для макро/микро)."""
    return [GoalOut.model_validate(g) for g in goals.list()]


@router.patch("/{goal_id}", response_model=GoalOut)
def set_goal_classification(
    goal_id: int,
    payload: GoalClassificationIn,
    goals: Annotated[GoalRepository, Depends(get_goal_repository)],
    db: DbSession,
) -> GoalOut:
    """Задать бизнес-классификацию цели (макро/микро). Только запись в БД, без
    внешних API."""
    goal = goals.get(goal_id)
    if goal is None:
        raise NotFoundError(f"Цель {goal_id} не найдена.")
    goal = goals.set_classification(
        goal, payload.is_conversion, payload.is_lead
    )
    db.commit()
    db.refresh(goal)
    return GoalOut.model_validate(goal)


@router.post("/sync", response_model=GoalSyncResult)
def sync_goals(
    import_service: Annotated[ImportService, Depends(get_import_service)],
) -> GoalSyncResult:
    """Обновить справочник целей из Яндекс Метрики."""
    return import_service.sync_goals()
