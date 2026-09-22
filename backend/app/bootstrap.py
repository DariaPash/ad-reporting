"""Создание bootstrap-администратора при старте контейнера (между миграциями и
запуском uvicorn).

Без него некому создать первого пользователя: POST /users доступен только
admin.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


def ensure_bootstrap_admin(db: Session) -> None:
    settings = get_settings()
    if (
        not settings.initial_admin_username
        or not settings.initial_admin_password
    ):
        return

    users = UserRepository(db)
    if users.exists_by_username(settings.initial_admin_username):
        return

    users.create(
        settings.initial_admin_username,
        hash_password(settings.initial_admin_password),
        role="admin",
    )
    db.commit()
    logger.info(
        "bootstrap admin '%s' created", settings.initial_admin_username
    )


if __name__ == "__main__":
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        ensure_bootstrap_admin(session)
    finally:
        session.close()
