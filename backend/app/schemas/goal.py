from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    counter_id: int
    metrika_goal_id: int
    name: str
    goal_type: str | None
    is_conversion: bool
    is_lead: bool
    updated_at: datetime.datetime


class GoalClassificationIn(BaseModel):
    """PATCH /goals/{id} – задать бизнес-классификацию цели.

    Технический тип цели не определяет её бизнес-роль, классификация задаётся
    вручную.
    """

    is_conversion: bool
    is_lead: bool


class GoalSyncResult(BaseModel):
    created: int
    updated: int
