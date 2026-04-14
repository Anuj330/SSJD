"""Razorpay payment gateway integration."""

import os
import hmac
import hashlib
from decimal import Decimal

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_account, require_admin
from app.models.payment import PaymentOrder, PaymentStatusEnum
from app.models.members import Member

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")


def _get_razorpay_client():
    if not RAZORPAY_KEY_ID or RAZORPAY_KEY_ID == "rzp_test_REPLACE_ME":
        raise HTTPException(503, "Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env")
    import razorpay
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_payment_order(
    purpose: str = Query(..., description="deposit, loan_repayment, share_purchase, rd_installment"),
    entity_id: int = Query(..., description="ID of the deposit/loan/etc"),
    amount: Decimal = Query(..., gt=0),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_account),
):
    """Create a Razorpay order for online payment."""
    member_id = current.member_id
    if current.role == "admin":
        member_id = entity_id  # admin creating on behalf — entity_id doubles as context

    if not member_id:
        raise HTTPException(400, "Member context required")

    client = _get_razorpay_client()

    # Razorpay expects amount in paise (smallest currency unit)
    amount_paise = int(amount * 100)

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "notes": {
            "purpose": purpose,
            "entity_id": str(entity_id),
            "member_id": str(member_id),
        },
    }

    try:
        rz_order = client.order.create(data=order_data)
    except Exception as e:
        raise HTTPException(502, f"Razorpay order creation failed: {str(e)}")

    payment = PaymentOrder(
        member_id=member_id,
        purpose=purpose,
        entity_id=entity_id,
        amount=amount,
        razorpay_order_id=rz_order["id"],
        status=PaymentStatusEnum.created,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "order_id": rz_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
        "payment_record_id": payment.id,
        "purpose": purpose,
        "entity_id": entity_id,
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

    # Verify signature
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
    return {
        "message": "Payment verified and processed",
        "status": "paid",
        "purpose": payment.purpose,
        "amount": payment.amount,
        **result,
    }


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

    return {}


async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Razorpay webhook handler for server-to-server payment notifications."""
    body = await request.body()
    sig = request.headers.get("X-Razorpay-Signature", "")

    if not sig:
        raise HTTPException(400, "Missing signature")

    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if expected != sig:
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
