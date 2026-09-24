"""Управление пользователями (admin-only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_user_repository, require_admin
from app.core.exceptions import ConflictError
from app.core.security import generate_password, hash_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserCreated, UserOut

router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=list[UserOut])
def list_users(
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in users.list()]


@router.post("", response_model=UserCreated, status_code=201)
def create_user(
    payload: UserCreate,
    users: Annotated[UserRepository, Depends(get_user_repository)],
    db: DbSession,
) -> UserCreated:
    """Пароль генерируется сервером и возвращается один раз в открытом виде.
    В БД попадает только bcrypt-хеш; пароль никуда не логируется."""
    if users.exists_by_username(payload.username):
        raise ConflictError(
            f"Пользователь «{payload.username}» уже существует."
        )

    plain_password = generate_password()
    user = users.create(
        payload.username, hash_password(plain_password), role=payload.role
    )
    db.commit()
    db.refresh(user)
    return UserCreated(
        **UserOut.model_validate(user).model_dump(), password=plain_password
    )
