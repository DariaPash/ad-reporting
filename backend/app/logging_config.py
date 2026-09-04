"""Настройка логирования.

В логи нельзя писать токены, заголовок Authorization, тела запросов/ответов
внешних API и персональные данные.
"""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        # Уже настроено (например, повторный вызов при тестах) – не дублировать
        # хендлеры.
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)

    # Библиотечные логгеры пониже уровнем, чтобы не шуметь SQL-запросами по
    # умолчанию.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
