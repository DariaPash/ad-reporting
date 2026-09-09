"""Типизированные ошибки домена и их отображение в HTTP-ответы без раскрытия
внутренних деталей."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Базовый класс ошибок приложения."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ValidationDomainError(DomainError):
    """Бизнес-валидация, которую не выразить через Pydantic (например,
    диапазон дат с учётом состояния БД)."""

    status_code = 422
    code = "validation_error"


class ExternalApiError(DomainError):
    """Ошибка обращения к Яндекс Директу/Метрике. Сообщение обязано быть
    безопасным: без токенов, заголовков и тел ответов."""

    status_code = 502
    code = "external_api_error"


class NotImplementedYetError(DomainError):
    """Функциональность ещё не реализована (контракт API зафиксирован)."""

    status_code = 501
    code = "not_implemented_yet"


class ConflictError(DomainError):
    """Нарушение уникальности бизнес-ключа (например, дублирующийся
    username)."""

    status_code = 409
    code = "conflict"


class ForbiddenError(DomainError):
    """Учётные данные верны, но роль не даёт доступа к admin-only эндпоинту
    (403 – недостаточно прав, в отличие от 401 – нет/неверные креды)."""

    status_code = 403
    code = "forbidden"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error_handler(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error(
                "domain error on %s %s: %s",
                request.method,
                request.url.path,
                exc.message,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )
