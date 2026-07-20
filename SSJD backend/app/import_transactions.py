"""Import legacy cooperative-society transactions from a CSV.

    python -m app.import_transactions "/path/Transactions - Transactions.csv" [--dry-run] [--reset]

CSV columns -> handling
    acno         -> member account number (member_profiles.membership_number)
    vhrno        -> voucher number (one journal entry per voucher per member)
    vhrdate      -> transaction date (dd/mm/yyyy); reference_month = 1st of that month
    particulars  -> remarks
    sm + cd + OD -> the member's monthly share deposit amount (= total). OD is NOT a
                    separate loan repayment — it is a component of the deposit.
    total        -> IGNORED — recalculated as sm + cd + OD (file totals are unreliable;
                    e.g. some rows show total=500 with sm=cd=OD=0).

Business rules honoured:
  * One share_transactions row per voucher, amount = sm + cd + OD (monthly_share_deposit).
  * share_holdings is a balance-only table — never gets per-row inserts; its balance
    is RECOMPUTED from share_transactions (the source of truth) at the end.
  * Idempotent: dedup keyed on (member_id, voucher_no); re-runs insert nothing new.
  * Transaction-safe: one DB transaction; any error rolls back. --dry-run reports only.
  * Append-only double-entry: each voucher gets a balanced JournalEntry (Dr Cash; Cr Share Capital).
  * Missing members and zero-value rows are skipped and reported.
  * --reset purges a prior legacy import (share/loan/journal rows) before re-importing.
"""

import argparse
import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from sqlalchemy import text

from app.core.database import SessionLocal
from app.models.member_profile import MemberProfile
from app.models.share import ShareHolding, ShareTransaction, SHARE_DEPOSIT, gen_share_txn_id
from app.models.ledger import (
    JournalEntry, JournalLine, AccountTypeEnum, EntryStatusEnum,
)
from app.services.ledger_service import get_or_create_account

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("import_transactions")

CASH_CODE = "CASH-001"
SHARE_CAPITAL_CODE = "SHARE-CAP-001"


@dataclass
class Summary:
    rows_total: int = 0
    rows_processed: int = 0
    deposits_created: int = 0
    journal_created: int = 0
    skipped_missing_member: int = 0
    skipped_zero: int = 0
    skipped_bad_data: int = 0
    duplicates: int = 0
    total_mismatches: int = 0
    deposit_amount: Decimal = field(default_factory=lambda: Decimal("0"))
    missing_acnos: set = field(default_factory=set)

    def log(self, dry_run):
        tag = "[DRY RUN] " if dry_run else ""
        logger.info("──────── %sIMPORT SUMMARY ────────", tag)
        logger.info("Rows in file ............ %d", self.rows_total)
        logger.info("Rows processed .......... %d", self.rows_processed)
        logger.info("Share deposits created .. %d  (₹%s)", self.deposits_created, self.deposit_amount)
        logger.info("Journal entries created . %d", self.journal_created)
        logger.info("Duplicates skipped ...... %d", self.duplicates)
        logger.info("Skipped: missing member . %d", self.skipped_missing_member)
        logger.info("Skipped: zero movement .. %d", self.skipped_zero)
        logger.info("Skipped: bad data ....... %d", self.skipped_bad_data)
        logger.info("CSV total != sm+cd+OD ... %d (CSV totals ignored)", self.total_mismatches)
        if self.missing_acnos:
            sample = ", ".join(sorted(str(a) for a in self.missing_acnos)[:15])
            logger.warning("Unmatched account numbers (%d): %s", len(self.missing_acnos), sample)
        logger.info("────────────────────────────────")


def parse_decimal(value):
    s = (value or "").strip().replace(",", "")
    if not s:
        return Decimal("0")
    try:
        d = Decimal(s)
        return d if d >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def parse_date(value):
    s = (value or "").strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def purge_legacy(db):
    """Remove a previous legacy import so it can be re-run cleanly."""
    db.execute(text("DELETE FROM journal_lines WHERE journal_entry_id IN "
                    "(SELECT id FROM journal_entries WHERE txn_type = 'legacy_import')"))
    db.execute(text("DELETE FROM share_transactions WHERE voucher_no IS NOT NULL"))
    db.execute(text("DELETE FROM loan_transactions"))
    db.execute(text("DELETE FROM journal_entries WHERE txn_type = 'legacy_import'"))
    logger.info("Purged previous legacy import (share/loan/journal rows).")


def run(path, dry_run=False, reset=False):
    db = SessionLocal()
    s = Summary()
    entry_cache = {}
    affected_members = set()

    try:
        if reset:
            purge_legacy(db)

        cash = get_or_create_account(db, CASH_CODE, "Cash / Bank", AccountTypeEnum.asset)
        share_cap = get_or_create_account(db, SHARE_CAPITAL_CODE, "Share Capital", AccountTypeEnum.equity)
        db.flush()
        cash_id, share_cap_id = cash.id, share_cap.id

        member_map = {
            str(num): mid
            for num, mid in db.query(MemberProfile.membership_number, MemberProfile.member_id)
            .filter(MemberProfile.membership_number.isnot(None)).all()
        }
        logger.info("Loaded %d member account numbers", len(member_map))

        existing_share = {
            (m, v) for m, v in db.query(ShareTransaction.member_id, ShareTransaction.voucher_no)
            .filter(ShareTransaction.voucher_no.isnot(None)).all()
        }

        def get_or_create_entry(txn_ref, description):
            if txn_ref in entry_cache:
                return entry_cache[txn_ref]
            entry = db.query(JournalEntry).filter(JournalEntry.txn_ref == txn_ref).first()
            if not entry:
                entry = JournalEntry(
                    txn_ref=txn_ref, txn_type="legacy_import",
                    description=(description or "")[:255] or None,
                    status=EntryStatusEnum.posted,
                )
                db.add(entry)
                db.flush()
                s.journal_created += 1
            entry_cache[txn_ref] = entry.id
            return entry.id

        # --- Pass 1: aggregate rows by (acno, voucher). A voucher may span several
        #     rows (e.g. a CD line + an OD line); the deposit is their combined sm+cd+OD. ---
        groups = {}  # (acno, voucher) -> {deposit, date, particulars}
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                s.rows_total += 1
                acno = (row.get("acno") or "").strip()
                voucher = (row.get("vhrno") or "").strip()
                sm = parse_decimal(row.get("sm"))
                cd = parse_decimal(row.get("cd"))
                od = parse_decimal(row.get("OD"))
                txn_date = parse_date(row.get("vhrdate"))
                particulars = (row.get("particulars") or "").strip() or None

                if None in (sm, cd, od) or not acno or not voucher or txn_date is None:
                    s.skipped_bad_data += 1
                    continue

                # SM = CD + OD. Fold the small 'sm' head into CD (compulsory) so the
                # per-txn CD+OD always equals the deposit amount.
                cd_part = sm + cd
                od_part = od
                deposit = cd_part + od_part  # monthly deposit = sm + cd + OD
                csv_total = parse_decimal(row.get("total"))
                if csv_total is not None and csv_total != deposit:
                    s.total_mismatches += 1

                g = groups.get((acno, voucher))
                if g is None:
                    groups[(acno, voucher)] = {"deposit": deposit, "cd": cd_part, "od": od_part,
                                               "date": txn_date, "particulars": particulars}
                else:
                    g["deposit"] += deposit
                    g["cd"] += cd_part
                    g["od"] += od_part
                    g["date"] = min(g["date"], txn_date)
                    g["particulars"] = g["particulars"] or particulars

        # --- Pass 2: one share deposit per (member, voucher) ---
        for (acno, voucher), g in groups.items():
            member_id = member_map.get(acno)
            if member_id is None:
                s.skipped_missing_member += 1
                s.missing_acnos.add(acno)
                continue
            deposit = g["deposit"]
            if deposit <= 0:
                s.skipped_zero += 1
                continue
            if (member_id, voucher) in existing_share:
                s.duplicates += 1
                continue

            txn_date = g["date"]
            ref_month = date(txn_date.year, txn_date.month, 1)
            entry_id = get_or_create_entry(f"VCH-{acno}-{voucher}", g["particulars"])

            db.add(ShareTransaction(
                transaction_id=gen_share_txn_id(), member_id=member_id,
                txn_type=SHARE_DEPOSIT, amount=deposit,
                cd_amount=g["cd"], od_amount=g["od"], txn_date=txn_date,
                reference_month=ref_month, voucher_no=voucher,
                journal_entry_id=entry_id, remarks=g["particulars"],
            ))
            db.add(JournalLine(journal_entry_id=entry_id, account_id=cash_id, dr_amount=deposit, cr_amount=Decimal("0")))
            db.add(JournalLine(journal_entry_id=entry_id, account_id=share_cap_id, dr_amount=Decimal("0"), cr_amount=deposit))

            existing_share.add((member_id, voucher))
            s.deposits_created += 1
            s.deposit_amount += deposit
            affected_members.add(member_id)
            s.rows_processed += 1

        # ensure a holding row exists for every affected member
        if affected_members:
            have = {m for (m,) in db.query(ShareHolding.member_id)
                    .filter(ShareHolding.member_id.in_(affected_members)).all()}
            for mid in affected_members - have:
                db.add(ShareHolding(member_id=mid, balance=Decimal("0")))
            db.flush()

        if dry_run:
            db.rollback()
            logger.info("[DRY RUN] rolled back — no changes written.")
        else:
            db.commit()
            db.execute(text(
                "UPDATE share_holdings h SET "
                "  balance = COALESCE((SELECT SUM(CASE WHEN t.txn_type = :wd THEN -t.amount "
                "     WHEN t.txn_type = :dep THEN t.amount ELSE 0 END) "
                "     FROM share_transactions t WHERE t.member_id = h.member_id), 0), "
                "  cd_balance = COALESCE((SELECT SUM(CASE WHEN t.txn_type = :wd THEN -t.cd_amount "
                "     WHEN t.txn_type = :dep THEN t.cd_amount ELSE 0 END) "
                "     FROM share_transactions t WHERE t.member_id = h.member_id), 0), "
                "  od_balance = COALESCE((SELECT SUM(CASE WHEN t.txn_type = :wd THEN -t.od_amount "
                "     WHEN t.txn_type = :dep THEN t.od_amount ELSE 0 END) "
                "     FROM share_transactions t WHERE t.member_id = h.member_id), 0)"
            ), {"wd": "withdrawal", "dep": SHARE_DEPOSIT})
            db.commit()
            logger.info("Recomputed share_holdings balances (SM / CD / OD) from share_transactions.")

        s.log(dry_run)
        return s
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.exception("Import failed — rolled back: %s", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Import legacy society transactions from CSV.")
    ap.add_argument("path", help="Path to the transactions CSV")
    ap.add_argument("--dry-run", action="store_true", help="Validate and report without writing")
    ap.add_argument("--reset", action="store_true", help="Purge a prior legacy import before importing")
    args = ap.parse_args()
    run(args.path, dry_run=args.dry_run, reset=args.reset)
