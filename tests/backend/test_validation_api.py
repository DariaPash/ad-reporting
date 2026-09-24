"""Тесты валидации входных данных на уровне API: код ответа и безопасность
сообщения об ошибке."""

from __future__ import annotations

import base64

from app.core.security import hash_password
from app.repositories.goal_repository import GoalRepository
from app.repositories.user_repository import UserRepository


def _admin_header(db_session) -> dict[str, str]:
    """Журнал операций доступен только роли admin – запросы идут от её
    имени."""
    UserRepository(db_session).create(
        "ops_admin_test", hash_password("admin-pass"), role="admin"
    )
    db_session.commit()
    raw = base64.b64encode(b"ops_admin_test:admin-pass").decode("ascii")
    return {"Authorization": f"Basic {raw}"}


def test_create_report_missing_dates_returns_422(client):
    response = client.post("/reports", json={"campaign_ids": [1]})

    assert response.status_code == 422
    assert "detail" in response.json()  # штатный формат валидации FastAPI


def test_create_report_date_from_after_date_to_returns_422(client):
    response = client.post(
        "/reports",
        json={
            "date_from": "2026-09-10",
            "date_to": "2026-09-01",
            "campaign_ids": [1],
        },
    )

    assert response.status_code == 422


def test_create_report_empty_campaign_ids_returns_422(client):
    response = client.post(
        "/reports",
        json={
            "date_from": "2026-09-01",
            "date_to": "2026-09-10",
            "campaign_ids": [],
        },
    )

    assert response.status_code == 422


def test_create_report_unknown_campaign_returns_404_not_422(client):
    """Синтаксически валидный запрос с несуществующим campaign_id – это
    доменная ошибка (404), а не ошибка формата (422)."""
    response = client.post(
        "/reports",
        json={
            "date_from": "2026-09-01",
            "date_to": "2026-09-10",
            "campaign_ids": [999999999],
        },
    )

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"


def test_set_goal_classification_missing_fields_returns_422(client):
    response = client.patch(
        "/goals/1", json={"is_conversion": True}
    )  # is_lead отсутствует

    assert response.status_code == 422


def test_set_goal_classification_unknown_id_returns_404(client):
    response = client.patch(
        "/goals/999999999", json={"is_conversion": True, "is_lead": False}
    )

    assert response.status_code == 404


def test_set_goal_classification_valid_request_updates_goal(
    client, db_session
):
    goal, _ = GoalRepository(db_session).upsert_from_metrika(
        55327960, 555, "Тестовая цель", "url"
    )
    db_session.flush()

    response = client.patch(
        f"/goals/{goal.id}", json={"is_conversion": True, "is_lead": False}
    )

    assert response.status_code == 200
    assert response.json()["is_conversion"] is True


def test_operations_invalid_status_returns_422(client, db_session):
    headers = _admin_header(db_session)
    response = client.get(
        "/operations", params={"status": "bogus"}, headers=headers
    )

    assert response.status_code == 422


def test_operations_valid_status_values_accepted(client, db_session):
    headers = _admin_header(db_session)
    for status in ("running", "success", "error"):
        response = client.get(
            "/operations", params={"status": status}, headers=headers
        )
        assert response.status_code == 200


def test_operations_forbidden_for_specialist(client, db_session):
    UserRepository(db_session).create(
        "ops_specialist_test", hash_password("bob-pass"), role="specialist"
    )
    db_session.commit()
    raw = base64.b64encode(b"ops_specialist_test:bob-pass").decode("ascii")

    response = client.get(
        "/operations", headers={"Authorization": f"Basic {raw}"}
    )

    assert response.status_code == 403


def test_export_invalid_format_returns_422(client, db_session):
    """Некорректный `format` отклоняется (422) на уровне сигнатуры роута, до
    вызова сервиса."""
    response = client.get("/reports/1/export", params={"format": "docx"})

    assert response.status_code == 422


def test_export_missing_format_returns_422(client):
    response = client.get("/reports/1/export")

    assert response.status_code == 422
