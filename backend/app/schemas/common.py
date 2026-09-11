from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Единый формат ошибки. Никогда не содержит токены, заголовки или тела
    внешних ответов."""

    code: str
    message: str


class HealthResponse(BaseModel):
    status: str
    database: str
