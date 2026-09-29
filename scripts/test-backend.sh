#!/usr/bin/env sh
# Тесты серверной части. Запускаются в отдельной базе ad_reporting_test,
# чтобы не затрагивать рабочие данные (каждый тест откатывает свою транзакцию).
set -e
cd "$(dirname "$0")/.."

docker compose up -d postgres
docker compose exec -T postgres sh -c '
  until pg_isready -U "$POSTGRES_USER" -q; do sleep 1; done
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_database WHERE datname = '\''ad_reporting_test'\''" | grep -q 1 \
    || createdb -U "$POSTGRES_USER" ad_reporting_test'

docker compose run --rm --no-deps \
  -e POSTGRES_DB=ad_reporting_test \
  -e ENABLE_SCHEDULED_SYNC=false \
  -v "$PWD/tests:/app/tests" \
  -v "$PWD/requirements-dev.txt:/app/requirements-dev.txt" \
  --entrypoint sh backend \
  -c "pip install -q --root-user-action=ignore -r /app/requirements-dev.txt && cd /app && python -m pytest tests -q $*"
