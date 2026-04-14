"""Background scheduler for automated tasks — interest accrual, overdue detection, EMI reminders."""

import logging
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.models.deposit import DepositAccount, DepositStatusEnum
from app.models.scheme import Scheme
from app.models.loan import LoanAccount, LoanRepayment, LoanStatusEnum, LoanProduct
from app.models.share import RDInstallment
from app.models.members import Member
from app.models.member_profile import MemberProfile
from app.models.ledger import (
    Account, JournalEntry, JournalLine,
    AccountTypeEnum, OwnerTypeEnum, EntryStatusEnum,
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _get_or_create_account(db, code, name, acct_type):
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        acct = Account(code=code, name=name, type=acct_type,
                       owner_type=OwnerTypeEnum.society, is_active=True)
        db.add(acct)
        db.flush()
    return acct


def _post_journal(db, txn_type, description, dr_id, cr_id, amount, created_by=None):
    import uuid
    txn_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    entry = JournalEntry(txn_ref=txn_ref, txn_type=txn_type, description=description,
                         created_by=created_by, status=EntryStatusEnum.posted)
    db.add(entry)
    db.flush()
    db.add(JournalLine(journal_entry_id=entry.id, account_id=dr_id,
                        dr_amount=amount, cr_amount=Decimal("0")))
    db.add(JournalLine(journal_entry_id=entry.id, account_id=cr_id,
                        dr_amount=Decimal("0"), cr_amount=amount))
    return entry


# ──────────────────────────────────────────────
#  Job 1: Daily Interest Accrual for All Active Deposits
# ──────────────────────────────────────────────

def daily_interest_accrual():
    """Calculate and post interest for all active deposits. Runs daily at 00:30."""
    logger.info("SCHEDULER: Starting daily interest accrual")
    db = SessionLocal()
    try:
        calc_date = date.today()
        deposits = db.query(DepositAccount).filter(
            DepositAccount.status == DepositStatusEnum.active
        ).all()

        processed = 0
        for dep in deposits:
            scheme = db.query(Scheme).filter(Scheme.id == dep.scheme_id).first()
            if not scheme:
                continue

            from_date = dep.last_interest_date or dep.opened_date
            if calc_date <= from_date:
                continue

            days = (calc_date - from_date).days
            rate = Decimal(str(scheme.interest_rate))
            interest = (dep.current_balance * rate * days / (Decimal("365") * Decimal("100"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)

            if interest <= 0:
                continue

            int_exp = _get_or_create_account(db, "INT-EXP-001", "Interest Expense", AccountTypeEnum.expense)
            _post_journal(db, "interest_credit",
                          f"Auto interest on {dep.account_number} for {days} days @ {rate}%",
                          int_exp.id, dep.ledger_account_id, interest)

            dep.interest_earned += interest
            dep.current_balance += interest
            dep.last_interest_date = calc_date
            processed += 1

            # Send notification
            try:
                member = db.query(Member).filter(Member.id == dep.member_id).first()
                profile = db.query(MemberProfile).filter(MemberProfile.member_id == dep.member_id).first()
                if member and profile and profile.email:
                    from app.services.email_service import notify_interest_credited
                    notify_interest_credited(profile.email, member.name, dep.account_number,
                                             float(interest), float(dep.current_balance))
            except Exception:
                pass

        db.commit()
        logger.info("SCHEDULER: Interest accrual done — %d deposits processed", processed)
    except Exception as e:
        db.rollback()
        logger.error("SCHEDULER: Interest accrual failed — %s", e)
    finally:
        db.close()


# ──────────────────────────────────────────────
#  Job 2: Mark Overdue EMIs + Send Reminders
# ──────────────────────────────────────────────

def check_overdue_emis():
    """Mark unpaid EMIs past due date as overdue. Runs daily at 01:00."""
    logger.info("SCHEDULER: Checking overdue EMIs")
    db = SessionLocal()
    try:
        today = date.today()

        # Mark overdue
        overdue = (db.query(LoanRepayment)
                   .filter(LoanRepayment.is_paid == False,
                           LoanRepayment.due_date < today,
                           LoanRepayment.is_overdue == False)
                   .all())

        for inst in overdue:
            inst.is_overdue = True

            # Send overdue notification
            try:
                loan = db.query(LoanAccount).filter(LoanAccount.id == inst.loan_id).first()
                member = db.query(Member).filter(Member.id == loan.member_id).first()
                profile = db.query(MemberProfile).filter(MemberProfile.member_id == loan.member_id).first()
                if member and profile and profile.email:
                    from app.services.email_service import notify_emi_overdue
                    notify_emi_overdue(profile.email, member.name, loan.loan_number,
                                       str(inst.due_date), float(inst.total_due))
            except Exception:
                pass

        # Send reminder for EMIs due in 3 days
        reminder_date = today + timedelta(days=3)
        upcoming = (db.query(LoanRepayment)
                    .filter(LoanRepayment.is_paid == False,
                            LoanRepayment.due_date == reminder_date)
                    .all())

        for inst in upcoming:
            try:
                loan = db.query(LoanAccount).filter(LoanAccount.id == inst.loan_id).first()
                member = db.query(Member).filter(Member.id == loan.member_id).first()
                profile = db.query(MemberProfile).filter(MemberProfile.member_id == loan.member_id).first()
                if member and profile and profile.email:
                    from app.services.email_service import notify_emi_reminder
                    notify_emi_reminder(profile.email, member.name, loan.loan_number,
                                         str(inst.due_date), float(inst.total_due))
            except Exception:
                pass

        db.commit()
        logger.info("SCHEDULER: Marked %d overdue, sent %d reminders", len(overdue), len(upcoming))
    except Exception as e:
        db.rollback()
        logger.error("SCHEDULER: Overdue check failed — %s", e)
    finally:
        db.close()


# ──────────────────────────────────────────────
#  Job 3: Mark Overdue RD Installments
# ──────────────────────────────────────────────

def check_overdue_rd():
    """Mark unpaid RD installments past due date as overdue. Runs daily at 01:30."""
    logger.info("SCHEDULER: Checking overdue RD installments")
    db = SessionLocal()
    try:
        today = date.today()
        overdue = (db.query(RDInstallment)
                   .filter(RDInstallment.is_paid == False,
                           RDInstallment.due_date < today,
                           RDInstallment.is_overdue == False)
                   .all())

        for inst in overdue:
            inst.is_overdue = True

        db.commit()
        logger.info("SCHEDULER: Marked %d RD installments overdue", len(overdue))
    except Exception as e:
        db.rollback()
        logger.error("SCHEDULER: RD overdue check failed — %s", e)
    finally:
        db.close()


# ──────────────────────────────────────────────
#  Job 4: Check Deposit Maturity
# ──────────────────────────────────────────────

def check_deposit_maturity():
    """Mark deposits that have reached maturity date. Runs daily at 02:00."""
    logger.info("SCHEDULER: Checking deposit maturity")
    db = SessionLocal()
    try:
        today = date.today()
        matured = (db.query(DepositAccount)
                   .filter(DepositAccount.status == DepositStatusEnum.active,
                           DepositAccount.maturity_date != None,
                           DepositAccount.maturity_date <= today)
                   .all())

        for dep in matured:
            dep.status = DepositStatusEnum.matured

        db.commit()
        logger.info("SCHEDULER: Marked %d deposits as matured", len(matured))
    except Exception as e:
        db.rollback()
        logger.error("SCHEDULER: Maturity check failed — %s", e)
    finally:
        db.close()


# ──────────────────────────────────────────────
#  Start / Stop
# ──────────────────────────────────────────────

def start_scheduler():
    """Register all jobs and start the scheduler."""
    if scheduler.running:
        return

    # Daily interest accrual — 00:30 AM
    scheduler.add_job(daily_interest_accrual, CronTrigger(hour=0, minute=30),
                      id="daily_interest", replace_existing=True,
                      misfire_grace_time=3600)

    # Overdue EMI check — 01:00 AM
    scheduler.add_job(check_overdue_emis, CronTrigger(hour=1, minute=0),
                      id="overdue_emis", replace_existing=True,
                      misfire_grace_time=3600)

    # Overdue RD check — 01:30 AM
    scheduler.add_job(check_overdue_rd, CronTrigger(hour=1, minute=30),
                      id="overdue_rd", replace_existing=True,
                      misfire_grace_time=3600)

    # Deposit maturity check — 02:00 AM
    scheduler.add_job(check_deposit_maturity, CronTrigger(hour=2, minute=0),
                      id="deposit_maturity", replace_existing=True,
                      misfire_grace_time=3600)

    scheduler.start()
    logger.info("SCHEDULER: Started with 4 cron jobs")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("SCHEDULER: Stopped")
