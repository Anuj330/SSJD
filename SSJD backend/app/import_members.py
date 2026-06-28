"""Import members from Personal.csv.

    python -m app.import_members /path/to/Personal.csv

CSV columns -> DB mapping:
    acno        -> MemberProfile.membership_number (the society account number)
    OpDate      -> MemberProfile.date_of_joining   (dd/mm/yyyy)
    acname      -> Member.name / MemberProfile.name (account holder name)
    fathername  -> MemberProfile.father_name
    emailid     -> MemberProfile.email
    mobileno    -> Member.phone / MemberProfile.phone_number
    Address     -> Member.address / MemberProfile.address
    AdhaarNo    -> MemberProfile.aadhar
    PanNo       -> MemberProfile.pan
    NomineeName -> MemberProfile.nominee1

Idempotent: a row is skipped if a profile with the same membership_number exists.
Placeholder values (Not mentioned / Required / W/o. / blank) are stored as NULL.
"""

import csv
import sys
from datetime import datetime

from app.core.database import SessionLocal
from app.models.members import Member
from app.models.member_profile import MemberProfile

PLACEHOLDERS = {"", "not mentioned", "required", "na", "n/a", "-", "w/o.", "w/o",
                "s/o.", "s/o", "d/o.", "d/o", "nil", "none"}


def clean(v):
    if v is None:
        return None
    s = str(v).strip()
    return None if s.lower() in PLACEHOLDERS else s


def parse_date(v):
    s = clean(v)
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def run(path):
    db = SessionLocal()
    created = skipped = 0
    # Phones already used (Member.phone is unique) — avoid collisions.
    used_phones = {p for (p,) in db.query(Member.phone).filter(Member.phone.isnot(None)).all()}
    existing_acnos = {n for (n,) in db.query(MemberProfile.membership_number)
                      .filter(MemberProfile.membership_number.isnot(None)).all()}
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                acno_raw = clean(row.get("acno"))
                acno = int(acno_raw) if acno_raw and acno_raw.isdigit() else None
                name = clean(row.get("acname"))
                if not name:
                    skipped += 1
                    continue
                if acno is not None and acno in existing_acnos:
                    skipped += 1
                    continue

                phone = clean(row.get("mobileno"))
                # Member.phone is unique — only keep the first occurrence; profile keeps the real one.
                member_phone = phone if phone and phone not in used_phones else None
                if member_phone:
                    used_phones.add(member_phone)

                address = clean(row.get("Address"))

                member = Member(name=name, phone=member_phone, address=address, is_active=True)
                db.add(member)
                db.flush()  # get member.id

                db.add(MemberProfile(
                    member_id=member.id,
                    name=name,
                    father_name=clean(row.get("fathername")),
                    membership_number=acno,
                    date_of_joining=parse_date(row.get("OpDate")),
                    email=clean(row.get("emailid")),
                    phone_number=phone,
                    address=address,
                    aadhar=clean(row.get("AdhaarNo")),
                    pan=clean(row.get("PanNo")),
                    nominee1=clean(row.get("NomineeName")),
                ))
                if acno is not None:
                    existing_acnos.add(acno)
                created += 1

        db.commit()
        print(f"✓ Imported {created} members ({skipped} skipped).")
        print(f"  Members in DB: {db.query(Member).count()} · Profiles: {db.query(MemberProfile).count()}")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"✗ Import failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "/tmp/Personal.csv")
