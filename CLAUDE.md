# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SSJD (Shramik Sahkari Jaivik Darshan) is a cooperative society management system. The backend is a FastAPI application with PostgreSQL, SQLAlchemy ORM, Alembic migrations, and JWT authentication. The frontend is a React (Vite) SPA with Tailwind CSS, Zustand state management, and Axios API layer.

## Quick Start (Docker)

From the repository root, `docker compose up --build` starts Postgres + backend +
frontend, runs migrations, and seeds an admin (`admin@ssjd.coop` / `changeme123`).
Frontend → http://localhost:3000, API/docs → http://localhost:8000/docs, Postgres
→ host port **5544**. Production Dockerfiles live in each app folder.

## Development Commands

All commands run from the `SSJD backend/` directory.

```bash
# Activate virtual environment
source linux_backend_env/bin/activate

# Install dependencies (use requirements-dev.txt to also get pytest)
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create the first admin user (idempotent; chicken-and-egg bootstrap)
python -m app.seed

# Run tests (in-memory SQLite, no Postgres needed)
pytest

# Run database migrations
cd app && alembic upgrade head

# Generate a new migration after model changes
cd app && alembic revision --autogenerate -m "description"

# Check migration history
cd app && alembic history
```

API docs available at `http://localhost:8000/docs` (Swagger UI).

### Frontend (`SSJD frontend/ssjd-app/`)

```bash
cd "SSJD frontend/ssjd-app"
npm install
npm run dev      # starts on http://localhost:3000
npm run build    # production build to dist/
```

Vite dev server proxies `/api`, `/auth`, `/societies`, `/users` to `http://localhost:8000`.

## Architecture

### Backend (`SSJD backend/app/`)

- **`main.py`** — FastAPI app entry point. Calls `setup_logging()`, registers the
  rate limiter (slowapi) + a global exception handler, configures CORS, and mounts
  three router groups: `api_router` (`/api/v1/*`), `auth.router` (`/auth/*`),
  `society.router` (`/societies/*`).
- **`api/urls.py`** — Central route registry for `/api/v1` endpoints using `router.add_api_route()`. New endpoints go here.
- **`api/`** — Route handlers: auth, members, member_profile, member_auth, ledger,
  society, users, schemes, deposits, loans, shares, reports, analytics, payments,
  pdf_exports, email, activity.
- **`models/`** — SQLAlchemy ORM models. All extend `Base` from `models/base.py`.
- **`schemas/`** — Pydantic request/response validation schemas.
- **`services/`** — Business logic: `ledger_service.py` (shared double-entry posting),
  `scheduler.py` (APScheduler daily jobs), `email_service.py` (Brevo), `pdf_service.py`
  (WeasyPrint), `auth_service.py`.
- **`core/`** — Configuration and utilities: database session (`database.py`), JWT helpers (`jwt.py`), password hashing (`security.py`), dependency injection (`dependencies.py`), rate limiter (`limiter.py`), logging (`logging.py`), middleware (`middleware.py`).
- **`seed.py`** — Bootstraps the first admin + default society (`python -m app.seed`).
- **`alembic/`** — Migration files. Config in `app/alembic.ini`; `env.py` reads
  `DATABASE_URL` from the environment.
- **Background jobs** (`services/scheduler.py`) — daily interest accrual, overdue
  EMI/RD detection + reminder emails, and deposit maturity checks.

### Key Domain: Double-Entry Ledger

The ledger system (`models/ledger.py`, `api/ledger.py`, `schemas/ledger.py`) implements double-entry bookkeeping:
- **Accounts** have types (asset, liability, income, expense, equity) and owners (society, member, system).
- **JournalEntry** records transactions with a unique `txn_ref` and status (posted/reversed).
- **JournalLine** holds debit/credit amounts (Numeric 14,2 in INR). Check constraints enforce exactly one side > 0.
- Posting validates total debits == total credits. Reversals create offset entries automatically.

### Authentication

Two auth flows (both login endpoints rate-limited to 5/minute per IP):
- **Admin/Staff**: `POST /auth/login` with a JSON body `{email, password}` → JWT token.
  Protected routes use the `require_admin` dependency (from `core/dependencies.py`).
- **Members**: `POST /api/v1/member/login` with JSON `{username, password}` → JWT token
  with `member_id` claim. Protected routes use the `require_member` dependency.

Unified auth lives in `core/dependencies.py` (`get_current_account` → `require_admin` /
`require_member`), with `role` + `user_id`/`member_id` JWT claims.

Passwords are SHA256 pre-hashed then bcrypt-hashed (handles arbitrary-length inputs).
**`bcrypt` is pinned to `<4.1`** in requirements — passlib 1.7.4 is incompatible with
bcrypt ≥ 4.1 and hashing breaks at runtime otherwise.

## Code Conventions

- **Absolute imports only** (e.g., `from app.models.user import User`, not relative imports).
- **Dependency injection** via FastAPI `Depends()` for DB sessions (`get_db`) and auth.
- **Enums** for fixed-choice fields (GenderEnum, AccountTypeEnum, OwnerTypeEnum, etc.).
- **Timezone-aware timestamps** with `TimestampMixin` on models.

## Database

PostgreSQL connection configured via `DATABASE_URL` (env var; see `.env.example`).
`.env` is gitignored — never commit it. The DB session uses `pool_pre_ping=True` for
connection health checks. Alembic `env.py` must import all models for autogenerate to
detect changes.

### Frontend (`SSJD frontend/ssjd-app/src/`)

- **`App.jsx`** — React Router route definitions. All app routes sit under a `ProtectedRoute` + `Layout` wrapper except `/login`.
- **`services/`** — Axios-based API layer. `api.js` is the shared Axios instance with auth interceptor and error handling. Domain services: `auth.js`, `members.js`, `profiles.js`, `ledger.js`.
- **`store/`** — Zustand stores: `authStore.js` (login/logout/token), `themeStore.js` (dark/light mode with localStorage persistence).
- **`components/ui/`** — Reusable primitives: Button, Input, Select, Card, Modal, DataTable (with sorting/pagination), Badge, Skeleton, EmptyState.
- **`components/layout/`** — Sidebar (navigation with section headings), Navbar (theme toggle, logout), Layout (responsive shell with Outlet).
- **`pages/`** — Route-based views: Dashboard, Members (list/detail/form/passbook),
  Profiles, Schemes, Deposits, Loans (products/list), Shares, Reports, Analytics,
  Payments, Ledger (Accounts, JournalEntry, TrialBalance, Statements), and member
  self-service (MyDeposits, MyLoans, MyShares).
- **`hooks/`** — `useApi` (generic fetch-with-state hook), `useDebounce`.

## Tests & CI

- **Tests**: `pytest` from `SSJD backend/` (in-memory SQLite, no Postgres needed).
  Coverage focuses on the ledger service (double-entry balancing, DB constraints) and
  password hashing. Add tests under `SSJD backend/tests/`.
- **CI**: `.github/workflows/ci.yml` runs backend pytest + frontend lint/build on push
  and PR.
