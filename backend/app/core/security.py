"""Хеширование паролей (bcrypt). Plaintext-пароли нигде не хранятся и не
логируются."""

from __future__ import annotations

import secrets

import bcrypt


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(
        plain_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def generate_password(length: int = 16) -> str:
    """Случайный пароль для нового пользователя. Показывается один раз,
    в открытом виде не сохраняется (сразу хешируется через hash_password)."""
    return secrets.token_urlsafe(length)
