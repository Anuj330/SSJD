# SSJD Cooperative — Website Backend & CMS

Enterprise Django + DRF backend and content-management system powering the
cooperative-society / banking website (design: *Cooperative Banking Website*).
All website content — banners, schemes, notices, branches, gallery, pages,
testimonials, leads, and global settings — is managed from the admin CMS and
served over a versioned REST API. **No code edits required to change content.**

> This is a standalone Django project. It is independent of the FastAPI
> member-management backend (`SSJD backend/`) — different stack, different purpose
> (public website vs. internal operations).

---

## Tech stack

| Concern | Choice |
|---|---|
| Framework | Django 5 + Django REST Framework |
| Auth | JWT (SimpleJWT) — access/refresh, rotation + blacklist |
| Database | PostgreSQL (UUID PKs, indexes, soft delete, audit) |
| Cache / broker | Redis |
| Background tasks | Celery + Celery beat |
| API docs | drf-spectacular (Swagger / ReDoc) |
| Rich text | django-ckeditor |
| Media | Local or S3 (django-storages) — switch via `MEDIA_STORAGE` |
| Server | gunicorn + WhiteNoise |

## Project structure

```
SSJD-website-cms/
├── config/                 # Django project (settings/urls/wsgi/asgi/celery)
│   └── settings/           # base.py · dev.py · prod.py
├── core/                   # Shared layer
│   ├── models.py           # BaseModel: UUID + timestamps + soft-delete + audit
│   ├── managers.py         # SoftDeleteManager / AllObjectsManager
│   ├── middleware.py       # thread-local current-user for audit stamping
│   ├── permissions.py      # IsStaffOrReadOnly / IsAdminOrReadOnly / HasRole
│   ├── pagination.py       # StandardResultsSetPagination
│   ├── validators.py       # image / document upload validation
│   └── admin.py            # BaseModelAdmin (soft-delete aware)
├── apps/
│   ├── accounts/           # Custom User (email login), roles, JWT, reset/verify
│   ├── banners/            # Hero slider (+ reorder action)
│   ├── schemes/            # FD / RD / Savings / Loan products
│   ├── notices/            # News & notices (PDF, pin, auto-expiry)
│   ├── branches/           # Branch locator (geo + map embed + manager)
│   ├── gallery/            # Albums + images
│   ├── pages/              # CMS pages (About, Chairman, Privacy, T&C) — rich text
│   ├── testimonials/       # Customer reviews
│   ├── contacts/           # Leads (public submit, staff read/export, email notify)
│   ├── sitesettings/       # Singleton: logo, social, contact, footer, SEO, analytics
│   └── dashboard/          # Aggregated stats + inquiry analytics
├── media/  static/  templates/
├── Dockerfile  docker-compose.yml  entrypoint.sh
└── requirements.txt  .env.example
```

## User roles

`Super Admin` · `Admin` · `Content Manager` · `Branch Manager` — see
`apps/accounts/models.Role`. Admin/Super Admin manage users; all staff roles
can manage content and read leads.

---

## Quick start (Docker)

```bash
cp .env.example .env          # then edit secrets
docker compose up --build
# API docs → http://localhost:8001/api/docs/
# Admin    → http://localhost:8001/admin/
```

Set `DJANGO_SUPERUSER_EMAIL` + `DJANGO_SUPERUSER_PASSWORD` in `.env` to auto-create
the first Super Admin on boot.

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # point POSTGRES_* at your DB; set REDIS_URL
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

(Without Redis running, set `CELERY_EAGER=True` and avoid throttled endpoints,
or run a local `redis-server`.)

---

## API

Base path: `/api/v1/`. Browse everything interactively at `/api/docs/`.

### Auth (`/api/v1/auth/`)
| Method | Path | Purpose |
|---|---|---|
| POST | `login/` | email + password → access/refresh + profile |
| POST | `refresh/` | refresh → new access |
| POST | `logout/` | blacklist refresh token |
| GET/PATCH | `me/` | current user |
| POST | `change-password/` | change own password |
| POST | `password-reset/` · `password-reset/confirm/` | reset flow |
| POST | `verify-email/` | email verification |
| CRUD | `users/` | user management (Admin+) |

### Content (public read · staff write)
`banners/` · `schemes/` · `notices/` (by slug) · `branches/` · `gallery/albums/` ·
`gallery/images/` · `pages/` (by slug) · `testimonials/` · `settings/`

### Leads
`POST contacts/` is public (rate-limited). Listing, filtering, status updates and
`GET contacts/export/` (CSV) are staff-only.

### Dashboard
`GET dashboard/stats/` — totals, inquiry statistics, recent notices, quick actions.

All list endpoints support **pagination** (`?page`, `?page_size`), **filtering**
(per-field), **search** (`?search=`), and **ordering** (`?ordering=`).

---

## Key design notes

- **UUID primary keys** everywhere (non-enumerable, safe in URLs).
- **Soft delete**: `obj.delete()` flags `is_deleted`; `Model.all_objects` sees
  everything; the admin can restore. Pass `hard=True` to truly delete.
- **Audit**: `created_by` / `updated_by` auto-stamped from the request user via
  `core.middleware.AuditUserMiddleware` — no view boilerplate.
- **Public vs staff visibility**: content viewsets hide inactive/unpublished/expired
  records from anonymous callers and show everything to staff.
- **Background tasks**: lead emails (`apps.contacts.tasks`) and daily notice
  auto-expiry (`apps.notices.tasks`, scheduled in `CELERY_BEAT_SCHEDULE`).
- **Media storage**: flip `MEDIA_STORAGE=s3` + AWS vars to move uploads to S3.

## Security

JWT auth with rotation + blacklist · CSRF/XSS/clickjacking middleware · HSTS +
secure cookies in prod · password hashing + validators · leads never publicly
readable.

### Hardening applied (audited)

- **No privilege escalation** — `/auth/me/` cannot change role/staff flags
  (`MeSerializer` locks them); only a Super Admin can grant the Super Admin role
  (`_RoleGuardMixin`); `is_superuser` is never exposed over the API.
- **Rate limiting enforced** — `ScopedRateThrottle` is active, so login
  (10/min, brute-force), contact form (5/min, spam) and password-reset (5/min,
  enumeration/email-abuse) limits are real, not just declared.
- **Upload safety** — images are verified to be real raster images (Pillow);
  PDFs are checked by magic bytes; SVG is disallowed (script-carrying → XSS).
- **Stored-XSS guard** — `branch.google_map_iframe` accepts only Google Maps
  embed iframes (blocks `<script>`/handler injection by non-admin staff).
- **CSV/formula injection** — lead exports neutralise cells starting with
  `= + - @`.
- **Prod boot guards** — refuses to start with a default `SECRET_KEY` or a
  wildcard `ALLOWED_HOSTS`.

> Trusted-admin note: `sitesettings.head_scripts` / `body_scripts` hold raw
> analytics snippets by design and are **Admin-only writable** — render them only
> in trusted contexts on the frontend.

## Status / next steps

Foundation is complete and verified: `manage.py check` passes, all 11 apps migrate
against Postgres, and the API smoke test (JWT login, role-gated CRUD, public
contact submission, lead export, dashboard, OpenAPI schema) is green.

Possible follow-ups: a `/api/v1/homepage/` aggregate endpoint, an EMI-calculator
endpoint, multi-language fields, WhatsApp/SMS integration, and swapping CKEditor 4
for `django-ckeditor-5` (CKEditor 4 carries a security advisory).
```
