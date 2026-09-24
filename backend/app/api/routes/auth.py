"""Внутренний эндпоинт для nginx `auth_request` – не публичный контракт API,
скрыт из /docs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.deps import get_current_user, get_user_repository
from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserOut

router = APIRouter(tags=["auth"])
security = HTTPBasic()


@router.get("/auth/verify", include_in_schema=False)
def verify_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> dict[str, str]:
    user = users.get_by_username(credentials.username)
    if user is None or not verify_password(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="Ad Reporting"'},
        )
    return {"status": "ok"}


@router.get("/auth/me", response_model=UserOut)
def get_me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    """Текущий пользователь и его роль – для отображения пунктов меню на
    фронтенде."""
    return UserOut.model_validate(user)
