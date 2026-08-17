"""Razorpay payment gateway integration."""

import os
import hmac
import hashlib
import uuid
from decimal import Decimal

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_account, require_admin
from app.models.payment import PaymentOrder, PaymentStatusEnum
from app.models.members import Member

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
# Webhooks are signed with the webhook's own secret (set in the Razorpay
# dashboard when you create the webhook), NOT the API key secret.
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


def _is_mock() -> bool:
    """Mock mode when Razorpay isn't configured, or PAYMENTS_MOCK is set —
    lets the full payment flow run end-to-end without a live gateway."""
    if os.getenv("PAYMENTS_MOCK", "").lower() in ("1", "true", "yes"):
        return True
    return not RAZORPAY_KEY_ID or RAZORPAY_KEY_ID in ("rzp_test_REPLACE_ME", "")


def _get_razorpay_client():
    import razorpay
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_payment_order(
    purpose: str = Query(..., description="deposit, loan_repayment, share_purchase, rd_installment"),
    entity_id: int = Query(..., description="ID of the deposit/loan/etc"),
    amount: Decimal = Query(..., gt=0),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    """Create a payment order (real Razorpay order, or a mock order in test mode)."""
    member_id = current.member_id
    if current.role == "admin":
        member_id = entity_id  # admin creating on behalf — entity_id doubles as context
    if not member_id:
        raise HTTPException(400, "Member context required")

    amount_paise = int(amount * 100)
    mock = _is_mock()

    if mock:
        order_id = f"order_mock_{uuid.uuid4().hex[:18]}"
    else:
        try:
            rz_order = _get_razorpay_client().order.create(data={
                "amount": amount_paise, "currency": "INR",
                "notes": {"purpose": purpose, "entity_id": str(entity_id), "member_id": str(member_id)},
            })
            order_id = rz_order["id"]
        except Exception as e:
            raise HTTPException(502, f"Razorpay order creation failed: {str(e)}")

    payment = PaymentOrder(
        member_id=member_id, purpose=purpose, entity_id=entity_id, amount=amount,
        razorpay_order_id=order_id, status=PaymentStatusEnum.created,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "razorpay_order_id": order_id,
        "amount_paise": amount_paise,
        "currency": "INR",
        "razorpay_key_id": RAZORPAY_KEY_ID,
        "payment_record_id": payment.id,
        "purpose": purpose,
        "entity_id": entity_id,
        "mock": mock,
    }


def verify_payment(
    razorpay_order_id: str = Query(...),
    razorpay_payment_id: str = Query(...),
    razorpay_signature: str = Query(...),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    """Verify Razorpay payment signature and mark as paid."""
    payment = db.query(PaymentOrder).filter(
        PaymentOrder.razorpay_order_id == razorpay_order_id
    ).first()

    if not payment:
        raise HTTPException(404, "Payment order not found")

    if payment.status == PaymentStatusEnum.paid:
        return {"message": "Payment already verified", "status": "paid"}

    # Mock orders skip signature verification (test mode, no live gateway).
    if not razorpay_order_id.startswith("order_mock_"):
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_sig = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        if expected_sig != razorpay_signature:
            payment.status = PaymentStatusEnum.failed
            db.commit()
            raise HTTPException(400, "Payment signature verification failed")

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = PaymentStatusEnum.paid

    # Process the payment based on purpose
    result = _process_payment(db, payment, current)

    db.commit()

    _notify_payment(db, payment)

    return {
        "message": "Payment verified and processed",
        "status": "paid",
        "purpose": payment.purpose,
        "amount": payment.amount,
        **result,
    }


def _notify_payment(db, payment):
    """Best-effort WhatsApp/SMS confirmation to the member (never blocks the payment)."""
    try:
        from app.services.notify_service import send_whatsapp
        from app.models.member_profile import MemberProfile
        mem = db.query(Member).filter(Member.id == payment.member_id).first()
        prof = db.query(MemberProfile).filter(MemberProfile.member_id == payment.member_id).first()
        phone = (mem.phone if mem else None) or (prof.phone_number if prof else None)
        if not (mem and phone):
            return
        label = {
            "share_purchase": "share money", "loan_repayment": "loan EMI",
            "deposit": "deposit", "rd_installment": "RD installment",
        }.get(payment.purpose, payment.purpose)
        msg = (f"Hi {mem.name}, SSJD Cooperative received your {label} payment of "
               f"Rs {payment.amount}. Thank you.")
        send_whatsapp(phone, msg)
    except Exception:
        pass


def _process_payment(db, payment: PaymentOrder, current: CurrentUser) -> dict:
    """After payment verification, execute the corresponding business operation."""
    from app.api.deposits import (
        _get_or_create_system_account, _post_journal,
        CASH_ACCOUNT_CODE,
    )
    from app.models.deposit import DepositAccount, DepositStatusEnum
    from app.models.loan import LoanAccount, LoanRepayment, LoanStatusEnum, LoanProduct
    from app.models.ledger import AccountTypeEnum
    from decimal import ROUND_HALF_UP
    from datetime import date

    if payment.purpose == "deposit":
        deposit = db.query(DepositAccount).filter(DepositAccount.id == payment.entity_id).first()
        if not deposit or deposit.status != DepositStatusEnum.active:
            return {"warning": "Deposit account not found or inactive — payment recorded but not applied"}

        cash = _get_or_create_system_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
        entry = _post_journal(db, "deposit", f"Online deposit to {deposit.account_number}",
                              cash.id, deposit.ledger_account_id, payment.amount, current.user_id)
        deposit.principal_amount += payment.amount
        deposit.current_balance += payment.amount
        payment.journal_entry_id = entry.id
        return {"new_balance": str(deposit.current_balance)}

    elif payment.purpose == "loan_repayment":
        loan = db.query(LoanAccount).filter(LoanAccount.id == payment.entity_id).first()
        if not loan or loan.status != LoanStatusEnum.active:
            return {"warning": "Loan not found or inactive"}

        cash = _get_or_create_system_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
        entry = _post_journal(db, "loan_repayment", f"Online repayment for {loan.loan_number}",
                              cash.id, loan.ledger_account_id, payment.amount, current.user_id)

        # Apply to next unpaid installment(s)
        remaining = payment.amount
        inst = (db.query(LoanRepayment)
                .filter(LoanRepayment.loan_id == loan.id, LoanRepayment.is_paid == False)
                .order_by(LoanRepayment.installment_no).first())

        while remaining > 0 and inst:
            needed = inst.total_due - inst.total_paid
            pay_now = min(remaining, needed)
            inst.total_paid += pay_now
            inst.paid_date = date.today()
            if inst.total_paid >= inst.total_due:
                inst.is_paid = True
            remaining -= pay_now
            loan.outstanding_principal -= min(pay_now, inst.principal_due - inst.principal_paid)
            inst.principal_paid = min(inst.principal_paid + pay_now, inst.principal_due)

            if inst.is_paid:
                inst = (db.query(LoanRepayment)
                        .filter(LoanRepayment.loan_id == loan.id, LoanRepayment.is_paid == False)
                        .order_by(LoanRepayment.installment_no).first())
            else:
                inst = None

        if loan.outstanding_principal <= 0:
            loan.outstanding_principal = Decimal("0")
            loan.status = LoanStatusEnum.closed
            loan.closed_date = date.today()

        payment.journal_entry_id = entry.id
        return {"outstanding": str(loan.outstanding_principal)}

    elif payment.purpose == "share_purchase":
        # Online monthly share-money deposit.
        from app.models.share import ShareHolding, ShareTransaction, SHARE_DEPOSIT, gen_share_txn_id
        from app.services.ledger_service import get_or_create_account, post_journal
        member = db.query(Member).filter(Member.id == payment.member_id).first()
        holding = db.query(ShareHolding).filter(ShareHolding.member_id == payment.member_id).first()
        if not holding:
            holding = ShareHolding(member_id=payment.member_id, balance=Decimal("0"))
            db.add(holding); db.flush()
        cash = get_or_create_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
        share_cap = get_or_create_account(db, "SHARE-CAP-001", "Share Capital", AccountTypeEnum.equity)
        entry = post_journal(db, SHARE_DEPOSIT, f"Online share money from {member.name if member else payment.member_id}",
                             cash.id, share_cap.id, payment.amount, current.user_id)
        holding.balance += payment.amount
        db.add(ShareTransaction(
            transaction_id=gen_share_txn_id(), member_id=payment.member_id, txn_type=SHARE_DEPOSIT,
            amount=payment.amount, txn_date=date.today(), journal_entry_id=entry.id,
            remarks="Online payment",
        ))
        payment.journal_entry_id = entry.id
        return {"new_balance": str(holding.balance)}

    elif payment.purpose == "rd_installment":
        deposit = db.query(DepositAccount).filter(DepositAccount.id == payment.entity_id).first()
        if not deposit or deposit.status != DepositStatusEnum.active:
            return {"warning": "RD account not found or inactive"}
        cash = _get_or_create_system_account(db, CASH_ACCOUNT_CODE, "Cash / Bank", AccountTypeEnum.asset)
        entry = _post_journal(db, "rd_installment", f"Online RD installment for {deposit.account_number}",
                              cash.id, deposit.ledger_account_id, payment.amount, current.user_id)
        deposit.current_balance += payment.amount
        payment.journal_entry_id = entry.id
        return {"new_balance": str(deposit.current_balance)}

    return {}


async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Razorpay webhook handler for server-to-server payment notifications."""
    body = await request.body()
    sig = request.headers.get("X-Razorpay-Signature", "")

    if not sig:
        raise HTTPException(400, "Missing signature")

    secret = RAZORPAY_WEBHOOK_SECRET or RAZORPAY_KEY_SECRET
    if not secret:
        raise HTTPException(503, "Webhook secret not configured")

    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, sig):
        raise HTTPException(400, "Invalid webhook signature")

    import json
    payload = json.loads(body)
    event = payload.get("event", "")

    if event == "payment.captured":
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        if order_id:
            payment = db.query(PaymentOrder).filter(
                PaymentOrder.razorpay_order_id == order_id
            ).first()
            if payment and payment.status != PaymentStatusEnum.paid:
                payment.razorpay_payment_id = payment_id
                payment.status = PaymentStatusEnum.paid
                db.commit()

    return {"status": "ok"}


def list_payments(
    member_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    """List payment orders."""
    q = db.query(PaymentOrder, Member.name.label("member_name")).join(
        Member, Member.id == PaymentOrder.member_id
    )

    if current.role == "member":
        q = q.filter(PaymentOrder.member_id == current.member_id)
    elif member_id:
        q = q.filter(PaymentOrder.member_id == member_id)

    if status:
        q = q.filter(PaymentOrder.status == status)

    rows = q.order_by(PaymentOrder.id.desc()).all()

    return [
        {
            "id": p.id, "member_id": p.member_id, "member_name": name,
            "purpose": p.purpose, "entity_id": p.entity_id,
            "amount": p.amount, "currency": p.currency,
            "razorpay_order_id": p.razorpay_order_id,
            "razorpay_payment_id": p.razorpay_payment_id,
            "status": p.status.value, "created_at": p.created_at,
        }
        for p, name in rows
    ]
