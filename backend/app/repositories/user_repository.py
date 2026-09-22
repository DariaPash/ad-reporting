from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self._db.scalars(stmt).one_or_none()

    def exists_by_username(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    def list(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        return list(self._db.scalars(stmt))

    def create(
        self, username: str, password_hash: str, role: str = "specialist"
    ) -> User:
        user = User(username=username, password_hash=password_hash, role=role)
        self._db.add(user)
        return user
