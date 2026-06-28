"""Create/refresh a demo admin and a demo member login.

    python -m app.seed_users

Idempotent: updates passwords if the accounts already exist.
  Admin  -> login at /auth/login with email admin@ssjd.coop / password 1234
  Member -> login at /api/v1/member/login with username member1 / password 1234
"""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.society import Society
from app.models.members import Member
from app.models.member_account import MemberAccount

ADMIN_EMAIL = "admin@ssjd.coop"
ADMIN_PASSWORD = "1234"
MEMBER_USERNAME = "member1"
MEMBER_PASSWORD = "1234"
MEMBER_NAME = "Member One"
MEMBER_PHONE = "9000000001"


def run():
    db = SessionLocal()
    try:
        # Society (admin + member belong to one).
        society = db.query(Society).first()
        if not society:
            society = Society(name="SSJD Cooperative Society", status="active")
            db.add(society)
            db.flush()

        # ---- Admin ----
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if admin:
            admin.password_hash = hash_password(ADMIN_PASSWORD)
            admin.is_active = True
            admin.role = "admin"
            print(f"✓ Updated admin password: {ADMIN_EMAIL}")
        else:
            admin = User(
                society_id=society.id,
                name="Administrator",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            print(f"✓ Created admin: {ADMIN_EMAIL}")

        # ---- Member record (member login must link to a Member) ----
        member = db.query(Member).filter(Member.phone == MEMBER_PHONE).first()
        if not member:
            member = Member(name=MEMBER_NAME, phone=MEMBER_PHONE, is_active=True)
            db.add(member)
            db.flush()
            print(f"✓ Created member record: {MEMBER_NAME} (#{member.id})")

        # ---- Member login account ----
        account = db.query(MemberAccount).filter(MemberAccount.username == MEMBER_USERNAME).first()
        if account:
            account.password_hash = hash_password(MEMBER_PASSWORD)
            account.is_active = True
            account.member_id = member.id
            print(f"✓ Updated member password: {MEMBER_USERNAME}")
        else:
            account = MemberAccount(
                member_id=member.id,
                username=MEMBER_USERNAME,
                password_hash=hash_password(MEMBER_PASSWORD),
                is_active=True,
            )
            db.add(account)
            print(f"✓ Created member login: {MEMBER_USERNAME}")

        db.commit()
        print("\nDone. Login credentials:")
        print(f"  Admin  -> /auth/login         email: {ADMIN_EMAIL}   password: {ADMIN_PASSWORD}")
        print(f"  Member -> /api/v1/member/login username: {MEMBER_USERNAME}   password: {MEMBER_PASSWORD}")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"✗ Failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
