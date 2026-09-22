"""Тесты управления пользователями: admin-only CRUD поверх общего HTTP Basic
гейта."""

from __future__ import annotations

import base64

from app.core.security import hash_password
from app.repositories.user_repository import UserRepository


def _basic_header(username: str, password: str) -> dict[str, str]:
    raw = f"{username}:{password}".encode("utf-8")
    return {"Authorization": f"Basic {base64.b64encode(raw).decode('ascii')}"}


def _make_admin(
    db_session, username: str = "admin", password: str = "admin-pass"
) -> None:
    UserRepository(db_session).create(
        username, hash_password(password), role="admin"
    )
    db_session.commit()


def _make_specialist(
    db_session, username: str = "bob", password: str = "bob-pass"
) -> None:
    UserRepository(db_session).create(
        username, hash_password(password), role="specialist"
    )
    db_session.commit()


def test_admin_can_create_user_and_receives_generated_password(
    client, db_session
):
    _make_admin(db_session)

    response = client.post(
        "/users",
        json={"username": "carol", "role": "specialist"},
        headers=_basic_header("admin", "admin-pass"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "carol"
    assert body["role"] == "specialist"
    assert isinstance(body["password"], str) and len(body["password"]) >= 16

    # созданными кредами действительно можно пройти общий Basic-гейт
    verify = client.get(
        "/auth/verify", headers=_basic_header("carol", body["password"])
    )
    assert verify.status_code == 200


def test_create_user_rejects_duplicate_username(client, db_session):
    _make_admin(db_session)
    client.post(
        "/users",
        json={"username": "carol", "role": "specialist"},
        headers=_basic_header("admin", "admin-pass"),
    )

    response = client.post(
        "/users",
        json={"username": "carol", "role": "specialist"},
        headers=_basic_header("admin", "admin-pass"),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_specialist_cannot_manage_users(client, db_session):
    _make_admin(db_session)
    _make_specialist(db_session)

    list_response = client.get(
        "/users", headers=_basic_header("bob", "bob-pass")
    )
    create_response = client.post(
        "/users",
        json={"username": "dave", "role": "specialist"},
        headers=_basic_header("bob", "bob-pass"),
    )

    assert list_response.status_code == 403
    assert list_response.json()["code"] == "forbidden"
    assert create_response.status_code == 403


def test_users_endpoints_require_credentials(client, db_session):
    _make_admin(db_session)

    response = client.get("/users")

    assert response.status_code == 401


def test_list_users_returns_created_accounts(client, db_session):
    _make_admin(db_session)
    _make_specialist(db_session)

    response = client.get(
        "/users", headers=_basic_header("admin", "admin-pass")
    )

    assert response.status_code == 200
    usernames = {u["username"] for u in response.json()}
    assert usernames == {"admin", "bob"}


def test_auth_me_reports_role(client, db_session):
    _make_admin(db_session)
    _make_specialist(db_session)

    admin_me = client.get(
        "/auth/me", headers=_basic_header("admin", "admin-pass")
    )
    bob_me = client.get("/auth/me", headers=_basic_header("bob", "bob-pass"))

    assert admin_me.json()["role"] == "admin"
    assert bob_me.json()["role"] == "specialist"
