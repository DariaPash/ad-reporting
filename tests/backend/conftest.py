"""Фикстуры backend-тестов: каждый тест выполняется в транзакции, откатываемой
по завершении."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import (
    models,
)  # noqa: E402,F401 – регистрирует таблицы в Base.metadata
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """На случай запуска тестов до `alembic upgrade head` – идемпотентно."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """`join_transaction_mode="create_savepoint"`: commit()/rollback() в
    тестируемом коде работают через SAVEPOINT и не затрагивают внешнюю
    транзакцию теста, которая целиком откатывается в конце."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
