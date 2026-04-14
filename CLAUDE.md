# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SSJD (Shramik Sahkari Jaivik Darshan) is a cooperative society management system. The backend is a FastAPI application with PostgreSQL, SQLAlchemy ORM, Alembic migrations, and JWT authentication. The frontend is a React (Vite) SPA with Tailwind CSS, Zustand state management, and Axios API layer.

## Development Commands

All commands run from the `SSJD backend/` directory.

```bash
# Activate virtual environment
source linux_backend_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

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

- **`main.py`** — FastAPI app entry point. Mounts three router groups: `api_router` (`/api/v1/*`), `auth.router` (`/auth/*`), `society.router` (`/societies/*`).
- **`api/urls.py`** — Central route registry for `/api/v1` endpoints using `router.add_api_route()`. New endpoints go here.
- **`api/`** — Route handlers (auth, members, member_profile, member_auth, ledger, society, users).
- **`models/`** — SQLAlchemy ORM models. All extend `Base` from `models/base.py`.
- **`schemas/`** — Pydantic request/response validation schemas.
- **`services/`** — Business logic (currently `auth_service.py`).
- **`core/`** — Configuration and utilities: database session (`database.py`), JWT helpers (`jwt.py`), password hashing (`security.py`), dependency injection (`dependencies.py`), logging (`logging.py`), middleware (`middleware.py`).
- **`alembic/`** — Migration files. Config in `alembic.ini` at `SSJD backend/` root.

### Key Domain: Double-Entry Ledger

The ledger system (`models/ledger.py`, `api/ledger.py`, `schemas/ledger.py`) implements double-entry bookkeeping:
- **Accounts** have types (asset, liability, income, expense, equity) and owners (society, member, system).
- **JournalEntry** records transactions with a unique `txn_ref` and status (posted/reversed).
- **JournalLine** holds debit/credit amounts (Numeric 14,2 in INR). Check constraints enforce exactly one side > 0.
- Posting validates total debits == total credits. Reversals create offset entries automatically.

### Authentication

Two auth flows:
- **Admin/Staff**: `POST /auth/login` with email/password → JWT token. Protected routes use `get_current_user()` dependency.
- **Members**: `POST /api/v1/member/login` with username/password → JWT token with `member_id` claim. Protected routes use `get_current_member()` dependency.

Passwords are SHA256 pre-hashed then bcrypt-hashed (handles arbitrary-length inputs).

## Code Conventions

- **Absolute imports only** (e.g., `from app.models.user import User`, not relative imports).
- **Dependency injection** via FastAPI `Depends()` for DB sessions (`get_db`) and auth.
- **Enums** for fixed-choice fields (GenderEnum, AccountTypeEnum, OwnerTypeEnum, etc.).
- **Timezone-aware timestamps** with `TimestampMixin` on models.

## Database

PostgreSQL connection configured via `DATABASE_URL` in `SSJD backend/.env`. The DB session uses `pool_pre_ping=True` for connection health checks. Alembic `env.py` must import all models for autogenerate to detect changes.

### Frontend (`SSJD frontend/ssjd-app/src/`)

- **`App.jsx`** — React Router route definitions. All app routes sit under a `ProtectedRoute` + `Layout` wrapper except `/login`.
- **`services/`** — Axios-based API layer. `api.js` is the shared Axios instance with auth interceptor and error handling. Domain services: `auth.js`, `members.js`, `profiles.js`, `ledger.js`.
- **`store/`** — Zustand stores: `authStore.js` (login/logout/token), `themeStore.js` (dark/light mode with localStorage persistence).
- **`components/ui/`** — Reusable primitives: Button, Input, Select, Card, Modal, DataTable (with sorting/pagination), Badge, Skeleton, EmptyState.
- **`components/layout/`** — Sidebar (navigation with section headings), Navbar (theme toggle, logout), Layout (responsive shell with Outlet).
- **`pages/`** — Route-based views: Dashboard, Members (list/detail/form), Profiles (list/form), Ledger (Accounts, JournalEntry, TrialBalance, Statements).
- **`hooks/`** — `useApi` (generic fetch-with-state hook), `useDebounce`.

## No Tests / No CI

There are currently no test files or CI/CD pipelines configured.
