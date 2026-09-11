from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import Goal


class GoalRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self) -> list[Goal]:
        return list(self._db.scalars(select(Goal).order_by(Goal.name)))

    def get(self, goal_id: int) -> Goal | None:
        return self._db.get(Goal, goal_id)

    def get_many(self, goal_ids: list[int]) -> list[Goal]:
        if not goal_ids:
            return []
        return list(
            self._db.scalars(select(Goal).where(Goal.id.in_(goal_ids)))
        )

    def set_classification(
        self, goal: Goal, is_conversion: bool, is_lead: bool
    ) -> Goal:
        goal.is_conversion = is_conversion
        goal.is_lead = is_lead
        return goal

    def get_by_metrika_id(
        self, counter_id: int, metrika_goal_id: int
    ) -> Goal | None:
        stmt = select(Goal).where(
            Goal.counter_id == counter_id,
            Goal.metrika_goal_id == metrika_goal_id,
        )
        return self._db.scalars(stmt).one_or_none()

    def upsert_from_metrika(
        self,
        counter_id: int,
        metrika_goal_id: int,
        name: str,
        goal_type: str | None,
    ) -> tuple[Goal, bool]:
        """Создаёт или обновляет цель из Метрики. Возвращает (цель,
        была_ли_создана). При создании is_conversion/is_lead = False: тип цели
        в API не определяет её бизнес-роль, классификация задаётся через PATCH
        /goals/{id}."""
        goal = self.get_by_metrika_id(counter_id, metrika_goal_id)
        if goal is None:
            goal = Goal(
                counter_id=counter_id,
                metrika_goal_id=metrika_goal_id,
                name=name,
                goal_type=goal_type,
            )
            self._db.add(goal)
            return goal, True
        goal.name = name
        goal.goal_type = goal_type
        return goal, False
