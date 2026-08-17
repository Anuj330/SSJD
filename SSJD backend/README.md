# SSJD Backend

FastAPI backend for **SSJD (Shramik Sahkari Jaivik Darshan)**, a cooperative
society management system: members, deposits (FD/RD/MIS/savings), loans, shares,
a double-entry general ledger, reports, analytics, payments (Razorpay), and email
notifications (Brevo).

## Stack

- **FastAPI** + **SQLAlchemy** ORM + **Alembic** migrations
- **PostgreSQL**
- **JWT** auth (admin + member flows), bcrypt password hashing
- **APScheduler** for daily jobs (interest accrual, overdue detection, maturity)
- **WeasyPrint** (PDF), **Razorpay** (payments), **Brevo** (email)

## Quick start (Docker — recommended)

From the repository root (one directory up):

```bash
docker compose up --build
```

This starts Postgres + backend + frontend, runs migrations, and seeds an admin.

- API / Swagger UI → http://localhost:8000/docs
- Default admin → `admin@ssjd.coop` / `changeme123` (change after first login)

## Local development (without Docker)

```bash
# From this directory (SSJD backend/)
python -m venv linux_backend_env
source linux_backend_env/bin/activate
pip install -r requirements-dev.txt   # use requirements.txt for runtime-only

cp .env.example .env                  # then fill in real values
# Set a strong JWT secret:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"

# Run migrations
cd app && alembic upgrade head && cd ..

# Create the first admin (idempotent)
python -m app.seed

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

All config comes from environment variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `JWT_SECRET_KEY` | Secret for signing JWTs (**required**) |
| `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` | Token algorithm / lifetime |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` | First-admin seed values |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Payments |
| `BREVO_API_KEY` / `BREVO_SENDER_EMAIL` / `BREVO_SENDER_NAME` | Email |

## Migrations

```bash
cd app
alembic upgrade head                          # apply
alembic revision --autogenerate -m "message"  # generate after model changes
alembic history                               # view history
```

`alembic/env.py` reads `DATABASE_URL` from the environment (overriding the
placeholder in `alembic.ini`) and imports all models for autogenerate.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests run against an in-memory SQLite DB (no Postgres needed) and cover the
ledger service (double-entry balancing, constraints) and password hashing.

## Architecture

```
app/
├── main.py            # app entry: routers, CORS, rate limiting, logging, error handlers
├── api/               # route handlers + urls.py (central route registry)
├── models/            # SQLAlchemy ORM models (extend Base)
├── schemas/           # Pydantic request/response models
├── services/          # business logic: ledger_service, scheduler, email, pdf, auth
├── core/              # database, jwt, security, dependencies, limiter, logging, middleware
├── alembic/           # migrations
└── seed.py            # first-admin bootstrap
```

### Authentication

- **Admin/Staff**: `POST /auth/login` (JSON `{email, password}`) → JWT. Protected
  routes use `require_admin`.
- **Members**: `POST /api/v1/member/login` (JSON `{username, password}`) → JWT with
  `member_id`. Protected routes use `require_member`.

Both login endpoints are rate-limited to 5/minute per IP.

### Double-entry ledger

`services/ledger_service.py` is the single source of truth for creating accounts
and posting balanced journal entries. Debits must equal credits; a DB check
constraint enforces exactly one side (debit or credit) per line.
