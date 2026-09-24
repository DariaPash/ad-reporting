"""Тесты HTTP Basic Auth."""

from __future__ import annotations

import base64

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository


def _basic_header(username: str, password: str) -> dict[str, str]:
    raw = f"{username}:{password}".encode("utf-8")
    return {"Authorization": f"Basic {base64.b64encode(raw).decode('ascii')}"}


def test_verify_succeeds_for_correct_credentials(client, db_session):
    UserRepository(db_session).create(
        "test_user", hash_password("correct-horse")
    )
    db_session.flush()

    response = client.get(
        "/auth/verify", headers=_basic_header("test_user", "correct-horse")
    )

    assert response.status_code == 200


def test_verify_rejects_wrong_password(client, db_session):
    UserRepository(db_session).create(
        "test_user", hash_password("correct-horse")
    )
    db_session.flush()

    response = client.get(
        "/auth/verify", headers=_basic_header("test_user", "wrong-password")
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")


def test_verify_rejects_unknown_username(client):
    response = client.get(
        "/auth/verify", headers=_basic_header("nobody", "anything")
    )

    assert response.status_code == 401


def test_verify_requires_credentials(client):
    response = client.get("/auth/verify")

    assert response.status_code == 401


def test_verify_error_response_never_contains_password_or_hash(
    client, db_session
):
    password_hash = hash_password("correct-horse")
    UserRepository(db_session).create("test_user", password_hash)
    db_session.flush()

    response = client.get(
        "/auth/verify", headers=_basic_header("test_user", "wrong-password")
    )

    assert "wrong-password" not in response.text
    assert password_hash not in response.text


def test_auth_route_is_hidden_from_openapi_schema(client):
    """/auth/verify – внутренний эндпоинт для nginx auth_request, не попадает в
    OpenAPI-схему."""
    schema = client.get("/openapi.json").json()

    assert "/auth/verify" not in schema["paths"]
