from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

UserRole = Literal["admin", "specialist"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole
    created_at: datetime.datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    role: UserRole = "specialist"


class UserCreated(UserOut):
    """Ответ на создание пользователя – единственный момент, когда пароль в
    открытом виде покидает сервер. Повторно его получить нельзя, только
    сбросить.
    """

    password: str
