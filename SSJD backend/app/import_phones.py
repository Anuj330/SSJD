"""Map phone numbers to members by the numeric code embedded in their name.

Member names look like "Mr. JUGESHWAR KUMAR(5281001)"; the CSV's account_no
(e.g. 5281001) matches that parenthetical code. Saves the phone to both the
member record and the member profile.

    python -m app.import_phones /tmp/phones.csv   # columns: account_no,name,phone
"""

import csv
import re
import sys

from app.core.database import SessionLocal
from app.models.members import Member
from app.models.member_profile import MemberProfile

CODE = re.compile(r"\((\d+)\)")


def clean_phone(v):
    d = re.sub(r"\D", "", str(v or ""))
    return d or None


def run(path):
    db = SessionLocal()
    matched = updated = skipped_no_match = skipped_no_phone = dup_phone = 0
    try:
        # Build code -> member_id from the parenthetical code in member names.
        code_to_member = {}
        for mid, name in db.query(MemberProfile.member_id, MemberProfile.name).all():
            m = CODE.search(name or "")
            if m:
                code_to_member[m.group(1)] = mid

        used_phones = {p for (p,) in db.query(Member.phone).filter(Member.phone.isnot(None)).all()}

        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                acc = str(row.get("account_no") or "").strip()
                phone = clean_phone(row.get("phone"))
                if not phone:
                    skipped_no_phone += 1
                    continue
                member_id = code_to_member.get(acc)
                if member_id is None:
                    skipped_no_match += 1
                    continue
                matched += 1

                # Profile always gets the phone.
                prof = db.query(MemberProfile).filter(MemberProfile.member_id == member_id).first()
                if prof:
                    prof.phone_number = phone

                # Member.phone is unique — only set if free.
                member = db.query(Member).filter(Member.id == member_id).first()
                if member:
                    if phone in used_phones and member.phone != phone:
                        dup_phone += 1  # keep on profile only
                    else:
                        member.phone = phone
                        used_phones.add(phone)
                updated += 1

        db.commit()
        print(f"✓ Matched {matched} · updated {updated} members")
        print(f"  Unmatched account_no: {skipped_no_match} · blank phone: {skipped_no_phone} · duplicate phone (profile-only): {dup_phone}")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"✗ Failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "/tmp/phones.csv")
