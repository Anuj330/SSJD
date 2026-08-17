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

Upsert: a member with the same membership_number (acno) is UPDATED with the CSV
values (non-placeholder fields only); new acnos are created.
Placeholder values (Not mentioned / Required / W/o. / blank) are stored as NULL /
skipped on update (existing value kept).
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
    created = updated = skipped = 0
    # Phones already used (Member.phone is unique) — avoid collisions.
    used_phones = {p for (p,) in db.query(Member.phone).filter(Member.phone.isnot(None)).all()}
    # acno -> existing MemberProfile (for upsert)
    profiles_by_acno = {p.membership_number: p for p in
                        db.query(MemberProfile).filter(MemberProfile.membership_number.isnot(None)).all()}
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                acno_raw = clean(row.get("acno"))
                acno = int(acno_raw) if acno_raw and acno_raw.isdigit() else None
                name = clean(row.get("acname"))
                if not name:
                    skipped += 1
                    continue

                phone = clean(row.get("mobileno"))
                father = clean(row.get("fathername"))
                dob = parse_date(row.get("OpDate"))
                email = clean(row.get("emailid"))
                address = clean(row.get("Address"))
                aadhar = clean(row.get("AdhaarNo"))
                pan = clean(row.get("PanNo"))
                nominee = clean(row.get("NomineeName"))

                existing = profiles_by_acno.get(acno) if acno is not None else None
                if existing:
                    # UPDATE: apply non-null CSV values, keep existing otherwise.
                    member = db.query(Member).filter(Member.id == existing.member_id).first()
                    existing.name = name
                    if member:
                        member.name = name
                        if address:
                            member.address = address
                        # only change phone if it's free (unique constraint)
                        if phone and phone not in used_phones and phone != member.phone:
                            if member.phone:
                                used_phones.discard(member.phone)
                            member.phone = phone
                            used_phones.add(phone)
                    if father:  existing.father_name = father
                    if dob:     existing.date_of_joining = dob
                    if email:   existing.email = email
                    if phone:   existing.phone_number = phone
                    if address: existing.address = address
                    if aadhar:  existing.aadhar = aadhar
                    if pan:     existing.pan = pan
                    if nominee: existing.nominee1 = nominee
                    updated += 1
                    continue

                # CREATE new member
                member_phone = phone if phone and phone not in used_phones else None
                if member_phone:
                    used_phones.add(member_phone)
                member = Member(name=name, phone=member_phone, address=address, is_active=True)
                db.add(member)
                db.flush()  # get member.id
                prof = MemberProfile(
                    member_id=member.id, name=name, father_name=father,
                    membership_number=acno, date_of_joining=dob, email=email,
                    phone_number=phone, address=address, aadhar=aadhar, pan=pan, nominee1=nominee,
                )
                db.add(prof)
                if acno is not None:
                    profiles_by_acno[acno] = prof
                created += 1

        db.commit()
        print(f"✓ Members: {created} created, {updated} updated, {skipped} skipped.")
        print(f"  Members in DB: {db.query(Member).count()} · Profiles: {db.query(MemberProfile).count()}")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"✗ Import failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "/tmp/Personal.csv")
