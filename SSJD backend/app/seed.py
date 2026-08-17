"""Bootstrap the first admin user (and a default society).

Solves the chicken-and-egg problem: POST /api/v1/users/ requires an existing
admin, so a fresh database has no way to create the first one through the API.

Run it directly:

    python -m app.seed

Configuration (environment variables):
    ADMIN_EMAIL      first admin's email     (default: admin@ssjd.local)
    ADMIN_PASSWORD   first admin's password  (default: changeme123)
    ADMIN_NAME       first admin's name      (default: Administrator)
    SOCIETY_NAME     default society name    (default: SSJD Cooperative Society)

The script is idempotent: it does nothing if an admin already exists.
"""

import os
import sys
import logging

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.society import Society

logger = logging.getLogger(__name__)


def seed_admin() -> None:
    db = SessionLocal()
    try:
        # Idempotent: bail out if any admin already exists.
        existing_admin = db.query(User).filter(User.role == "admin").first()
        if existing_admin:
            logger.info("Admin already exists (%s) — nothing to seed.", existing_admin.email)
            print(f"✓ Admin already exists: {existing_admin.email}")
            return

        email = os.getenv("ADMIN_EMAIL", "admin@ssjd.coop")
        password = os.getenv("ADMIN_PASSWORD", "changeme123")
        name = os.getenv("ADMIN_NAME", "Administrator")
        society_name = os.getenv("SOCIETY_NAME", "SSJD Cooperative Society")

        # Reuse an existing society if present, otherwise create a default one.
        society = db.query(Society).first()
        if not society:
            society = Society(name=society_name, status="active")
            db.add(society)
            db.flush()
            logger.info("Created default society: %s", society_name)

        admin = User(
            society_id=society.id,
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()

        logger.info("Seeded first admin: %s", email)
        print(f"✓ Created admin: {email}")
        print("  ⚠️  Change this password after first login.")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.error("Admin seed failed: %s", exc)
        print(f"✗ Admin seed failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
