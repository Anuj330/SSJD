# ── SSJD Backend (production) ───────────────────────────────────────────────
# FastAPI + SQLAlchemy + Alembic. Runs DB migrations on boot, then serves with
# uvicorn. WeasyPrint (PDF export) needs the pango/cairo system libraries below.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System libraries required by WeasyPrint (PDF generation) + psycopg2 runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-dejavu \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Install Python deps first for layer caching.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Application code.
COPY app ./app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run as non-root. Pre-create the Aadhaar storage dir owned by appuser so a fresh
# named volume mounted there inherits writable ownership.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data/aadhaar \
    && chown -R appuser:appuser /code /data
USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
