"""Тесты панели мониторинга: проверка доступности внешних API (admin-only)."""

from __future__ import annotations

import base64

import pytest

from app.api.deps import get_direct_client, get_metrika_client
from app.core.exceptions import ExternalApiError
from app.core.security import hash_password
from app.main import app
from app.repositories.user_repository import UserRepository


def _basic_header(username: str, password: str) -> dict[str, str]:
    raw = f"{username}:{password}".encode("utf-8")
    return {"Authorization": f"Basic {base64.b64encode(raw).decode('ascii')}"}


def _make_admin(db_session) -> None:
    UserRepository(db_session).create(
        "admin", hash_password("admin-pass"), role="admin"
    )
    db_session.commit()


def _make_specialist(db_session) -> None:
    UserRepository(db_session).create(
        "bob", hash_password("bob-pass"), role="specialist"
    )
    db_session.commit()


class _OkClient:
    def get_campaigns(self):
        return []

    def get_counters(self):
        return []


class _FailingClient:
    def get_campaigns(self):
        raise ExternalApiError("Яндекс.Директ недоступен.")

    def get_counters(self):
        raise ExternalApiError("Яндекс.Метрика недоступна.")


@pytest.fixture
def override_yandex_clients():
    """Подменяет клиентов Директа/Метрики на фейковые (только для тестов
    мониторинга)."""
    state = {"ok": True}

    def _get_direct():
        return _OkClient() if state["ok"] else _FailingClient()

    def _get_metrika():
        return _OkClient() if state["ok"] else _FailingClient()

    app.dependency_overrides[get_direct_client] = _get_direct
    app.dependency_overrides[get_metrika_client] = _get_metrika
    try:
        yield state
    finally:
        app.dependency_overrides.pop(get_direct_client, None)
        app.dependency_overrides.pop(get_metrika_client, None)


def test_api_check_requires_admin(client, db_session, override_yandex_clients):
    _make_admin(db_session)
    _make_specialist(db_session)

    specialist_response = client.post(
        "/monitoring/api-check", headers=_basic_header("bob", "bob-pass")
    )
    anon_response = client.post("/monitoring/api-check")

    assert specialist_response.status_code == 403
    assert anon_response.status_code == 401


def test_api_check_reports_ok_for_both_services(
    client, db_session, override_yandex_clients
):
    _make_admin(db_session)

    response = client.post(
        "/monitoring/api-check", headers=_basic_header("admin", "admin-pass")
    )

    assert response.status_code == 200
    assert response.json() == {"direct": "ok", "metrika": "ok"}


def test_api_check_reports_error_and_logs_operation(
    client, db_session, override_yandex_clients
):
    _make_admin(db_session)
    override_yandex_clients["ok"] = False

    response = client.post(
        "/monitoring/api-check", headers=_basic_header("admin", "admin-pass")
    )
    assert response.json() == {"direct": "error", "metrika": "error"}

    operations = client.get(
        "/operations", headers=_basic_header("admin", "admin-pass")
    ).json()
    assert operations[0]["operation_type"] == "Проверка доступности API"
    assert operations[0]["status"] == "error"
