"""Create/refresh member login accounts for all imported members.

    python -m app.create_member_logins [output_csv_path]

  username = "SSJD" + zero-padded account number  (e.g. acno 1 -> SSJD0001)
  password = 1234 (shared temporary password — members should change it later)

Idempotent: creates an account if missing, otherwise updates the existing
account's username to the SSJD format. Writes a credentials CSV
(Account No, Name, Username, Password) so staff can distribute logins.
"""

import csv
import sys

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.member_profile import MemberProfile
from app.models.member_account import MemberAccount

DEFAULT_PASSWORD = "1234"


def username_for(acno):
    return f"SSJD{int(acno):04d}"


def run(out_path="/tmp/member-credentials.csv"):
    db = SessionLocal()
    created = updated = 0
    pw_hash = hash_password(DEFAULT_PASSWORD)  # same password → reuse one hash for all
    rows = []
    try:
        accounts_by_member = {a.member_id: a for a in db.query(MemberAccount).all()}

        profiles = (db.query(MemberProfile)
                    .filter(MemberProfile.membership_number.isnot(None))
                    .order_by(MemberProfile.membership_number).all())

        for p in profiles:
            username = username_for(p.membership_number)
            existing = accounts_by_member.get(p.member_id)
            if existing:
                existing.username = username
                existing.is_active = True
                updated += 1
            else:
                db.add(MemberAccount(
                    member_id=p.member_id,
                    username=username,
                    password_hash=pw_hash,
                    is_active=True,
                ))
                created += 1
            rows.append([p.membership_number, p.name, username, DEFAULT_PASSWORD])

        db.commit()

        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Account No", "Name", "Username", "Password"])
            w.writerows(rows)

        print(f"✓ {created} created, {updated} updated to SSJD format.")
        print(f"  Total member accounts: {db.query(MemberAccount).count()}")
        print(f"  Credentials written to: {out_path}")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"✗ Failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "/tmp/member-credentials.csv")
