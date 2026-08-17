#!/usr/bin/env bash
# Apply Alembic migrations, then exec the container command (uvicorn).
# alembic.ini lives in app/, so migrations run from there. env.py reads
# DATABASE_URL from the environment, so no .env file is required in the image.
set -euo pipefail

echo "[entrypoint] Running database migrations..."
( cd /code/app && alembic upgrade head )

# Optionally seed the first admin (idempotent). Enable with SEED_ADMIN=true.
if [ "${SEED_ADMIN:-false}" = "true" ]; then
    echo "[entrypoint] Seeding admin user..."
    python -m app.seed
fi

echo "[entrypoint] Starting application..."
exec "$@"
