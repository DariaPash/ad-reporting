#!/usr/bin/env sh
set -e

echo "Waiting for PostgreSQL..."
python -c "
import time
import sys
from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
for attempt in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('PostgreSQL is up')
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f'  attempt {attempt + 1}/30: {exc}')
        time.sleep(2)
print('PostgreSQL did not become ready in time', file=sys.stderr)
sys.exit(1)
"

echo "Running migrations..."
python -m alembic upgrade head

echo "Ensuring bootstrap admin (if configured)..."
python -m app.bootstrap

echo "Starting API..."
exec uvicorn app.main:app --host "${BACKEND_HOST:-0.0.0.0}" --port "${BACKEND_PORT:-8000}"
