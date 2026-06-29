#!/usr/bin/env bash
set -e

# Wait for Postgres.
if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT…"
  until nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do sleep 1; done
fi

# Only the web service runs migrations/collectstatic (celery workers skip them).
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying migrations…"
  python manage.py migrate --noinput

  echo "Collecting static…"
  python manage.py collectstatic --noinput
fi

# Create the first super admin if configured (idempotent).
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
e = '$DJANGO_SUPERUSER_EMAIL'
if not U.objects.filter(email=e).exists():
    U.objects.create_superuser(email=e, password='$DJANGO_SUPERUSER_PASSWORD', full_name='Super Admin')
    print('Created superuser', e)
"
fi

exec "$@"
