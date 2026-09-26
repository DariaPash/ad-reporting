"""Тесты app/scheduler.py: фоновый поток не должен стартовать по умолчанию."""

from __future__ import annotations

import threading

from app.config import get_settings
from app.scheduler import start_background_sync


def test_disabled_by_default_does_not_start_thread():
    get_settings.cache_clear()
    before = {t.name for t in threading.enumerate()}

    start_background_sync()

    after = {t.name for t in threading.enumerate()}
    assert "campaigns-goals-sync" not in after
    assert after == before
