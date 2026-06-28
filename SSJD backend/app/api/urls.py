from fastapi import APIRouter
from app.api import users, auth, members, member_profile, member_auth, ledger, schemes, deposits, loans, shares, reports, activity, analytics, payments, pdf_exports, email, aadhaar, messaging


router = APIRouter(prefix="/api/v1")

# Users
router.add_api_route(
    "/users/",
    users.create_user,
    methods=["POST"],
    response_model=None,
    tags=["Users"],
)

# Members
router.add_api_route(
    "/members/",
    members.create_member,
    methods=["POST"],
    tags=["Members"],
)

router.add_api_route(
    "/members/",
    members.list_members,
    methods=["GET"],
    tags=["Members"],
)

router.add_api_route(
    "/members/{member_id}",
    members.get_member,
    methods=["GET"],
    tags=["Members"],
)

router.add_api_route(
    "/members/{member_id}",
    members.update_member,
    methods=["PUT"],
    tags=["Members"],
)

router.add_api_route(
    "/members/{member_id}",
    members.deactivate_member,
    methods=["DELETE"],
    tags=["Members"],
)

router.add_api_route(
    "/members/{member_id}/reactivate",
    members.reactivate_member,
    methods=["POST"],
    tags=["Members"],
)

# Member Profiles
router.add_api_route(
    "/member-profiles/",
    member_profile.create_member_profile,
    methods=["POST"],
    tags=["Member Profiles"],
)

router.add_api_route(
    "/member-profiles/",
    member_profile.list_member_profiles,
    methods=["GET"],
    tags=["Member Profiles"],
)

router.add_api_route(
    "/member-profiles/{profile_id}",
    member_profile.get_member_profile,
    methods=["GET"],
    tags=["Member Profiles"],
)

router.add_api_route(
    "/member-profiles/{profile_id}",
    member_profile.update_member_profile,
    methods=["PUT"],
    tags=["Member Profiles"],
)

# Member Auth
router.add_api_route(
    "/member/register",
    member_auth.member_register,
    methods=["POST"],
    tags=["Member Auth"],
)

router.add_api_route(
    "/member/login",
    member_auth.member_login,
    methods=["POST"],
    tags=["Member Auth"],
)

# Ledger
router.add_api_route(
    "/ledger/accounts/",
    ledger.create_account,
    methods=["POST"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/journal/post",
    ledger.post_journal,
    methods=["POST"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/journal/{entry_id}/reverse",
    ledger.reverse_journal,
    methods=["POST"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/accounts/{account_id}/statement",
    ledger.account_statement,
    methods=["GET"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/trial-balance",
    ledger.trial_balance,
    methods=["GET"],
    tags=["Ledger"],
)

router.add_api_route(
    "/members/{member_id}/money-flow",
    ledger.member_money_flow,
    methods=["GET"],
    tags=["Ledger"],
)

router.add_api_route(
    "/members/{member_id}/passbook",
    ledger.member_passbook,
    methods=["GET"],
    tags=["Ledger"],
)

# Schemes
router.add_api_route(
    "/schemes/",
    schemes.create_scheme,
    methods=["POST"],
    tags=["Schemes"],
)

router.add_api_route(
    "/schemes/",
    schemes.list_schemes,
    methods=["GET"],
    tags=["Schemes"],
)

router.add_api_route(
    "/schemes/{scheme_id}",
    schemes.get_scheme,
    methods=["GET"],
    tags=["Schemes"],
)

router.add_api_route(
    "/schemes/{scheme_id}",
    schemes.update_scheme,
    methods=["PUT"],
    tags=["Schemes"],
)

# Deposits
router.add_api_route(
    "/deposits/open",
    deposits.open_deposit,
    methods=["POST"],
    tags=["Deposits"],
)

router.add_api_route(
    "/deposits/",
    deposits.list_deposits,
    methods=["GET"],
    tags=["Deposits"],
)

router.add_api_route(
    "/deposits/{deposit_id}",
    deposits.get_deposit,
    methods=["GET"],
    tags=["Deposits"],
)

router.add_api_route(
    "/deposits/{deposit_id}/deposit",
    deposits.deposit_money,
    methods=["POST"],
    tags=["Deposits"],
)

router.add_api_route(
    "/deposits/{deposit_id}/withdraw",
    deposits.withdraw_money,
    methods=["POST"],
    tags=["Deposits"],
)

router.add_api_route(
    "/deposits/{deposit_id}/close",
    deposits.close_deposit,
    methods=["POST"],
    tags=["Deposits"],
)

router.add_api_route(
    "/deposits/{deposit_id}/calculate-interest",
    deposits.calculate_interest,
    methods=["POST"],
    tags=["Deposits"],
)

router.add_api_route(
    "/deposits/{deposit_id}/statement",
    deposits.deposit_statement,
    methods=["GET"],
    tags=["Deposits"],
)

# Loan Products
router.add_api_route("/loan-products/", loans.create_loan_product, methods=["POST"], tags=["Loans"])
router.add_api_route("/loan-products/", loans.list_loan_products, methods=["GET"], tags=["Loans"])
router.add_api_route("/loan-products/{product_id}", loans.get_loan_product, methods=["GET"], tags=["Loans"])
router.add_api_route("/loan-products/{product_id}", loans.update_loan_product, methods=["PUT"], tags=["Loans"])

# Loan Operations
router.add_api_route("/loans/apply", loans.apply_loan, methods=["POST"], tags=["Loans"])
router.add_api_route("/loans/", loans.list_loans, methods=["GET"], tags=["Loans"])
router.add_api_route("/loans/{loan_id}", loans.get_loan, methods=["GET"], tags=["Loans"])
router.add_api_route("/loans/{loan_id}/approve", loans.approve_loan, methods=["POST"], tags=["Loans"])
router.add_api_route("/loans/{loan_id}/reject", loans.reject_loan, methods=["POST"], tags=["Loans"])
router.add_api_route("/loans/{loan_id}/disburse", loans.disburse_loan, methods=["POST"], tags=["Loans"])
router.add_api_route("/loans/{loan_id}/repay", loans.make_repayment, methods=["POST"], tags=["Loans"])
router.add_api_route("/loans/{loan_id}/schedule", loans.get_loan_schedule, methods=["GET"], tags=["Loans"])

# Shares
router.add_api_route("/members/{member_id}/shares", shares.get_member_shares, methods=["GET"], tags=["Shares"])
router.add_api_route("/members/{member_id}/shares/purchase", shares.purchase_shares, methods=["POST"], tags=["Shares"])
router.add_api_route("/members/{member_id}/shares/refund", shares.refund_shares, methods=["POST"], tags=["Shares"])
router.add_api_route("/shares/", shares.list_all_shares, methods=["GET"], tags=["Shares"])
router.add_api_route("/members/{member_id}/share-interest", shares.share_interest, methods=["GET"], tags=["Shares"])

# RD Installments
router.add_api_route("/deposits/{deposit_id}/rd/generate", shares.generate_rd_installments, methods=["POST"], tags=["RD"])
router.add_api_route("/deposits/{deposit_id}/rd/pay", shares.pay_rd_installment, methods=["POST"], tags=["RD"])
router.add_api_route("/deposits/{deposit_id}/rd/schedule", shares.get_rd_schedule, methods=["GET"], tags=["RD"])

# Reports
router.add_api_route("/reports/profit-loss", reports.profit_and_loss, methods=["GET"], tags=["Reports"])
router.add_api_route("/reports/balance-sheet", reports.balance_sheet, methods=["GET"], tags=["Reports"])
router.add_api_route("/reports/cash-flow", reports.cash_flow, methods=["GET"], tags=["Reports"])
router.add_api_route("/reports/member-outstanding", reports.member_outstanding, methods=["GET"], tags=["Reports"])
router.add_api_route("/reports/batch-interest", reports.batch_interest, methods=["POST"], tags=["Reports"])

# Activity Log
router.add_api_route("/activity-logs/", activity.list_activity_logs, methods=["GET"], tags=["Activity"])

# Receipts
router.add_api_route("/receipts/{entry_id}", activity.get_receipt, methods=["GET"], tags=["Receipts"])

# Analytics & Dividends
router.add_api_route("/analytics/dashboard", analytics.dashboard_kpis, methods=["GET"], tags=["Analytics"])
router.add_api_route("/analytics/overview", analytics.dashboard_overview, methods=["GET"], tags=["Analytics"])
router.add_api_route("/analytics/dividend", analytics.calculate_dividend, methods=["POST"], tags=["Analytics"])

# Payments (Razorpay)
router.add_api_route("/payments/create-order", payments.create_payment_order, methods=["POST"], tags=["Payments"])
router.add_api_route("/payments/verify", payments.verify_payment, methods=["POST"], tags=["Payments"])
router.add_api_route("/payments/webhook", payments.payment_webhook, methods=["POST"], tags=["Payments"])
router.add_api_route("/payments/", payments.list_payments, methods=["GET"], tags=["Payments"])

# Messaging (SMS / WhatsApp)
router.add_api_route("/messaging/status", messaging.messaging_status, methods=["GET"], tags=["Messaging"])
router.add_api_route("/messaging/contacts", messaging.list_contacts, methods=["GET"], tags=["Messaging"])
router.add_api_route("/messaging/send", messaging.send_message, methods=["POST"], tags=["Messaging"])
router.add_api_route("/messaging/send-bulk", messaging.send_bulk, methods=["POST"], tags=["Messaging"])

# Email Notifications
router.add_api_route("/email/members", email.list_members_with_email, methods=["GET"], tags=["Email"])
router.add_api_route("/email/send", email.send_notification, methods=["POST"], tags=["Email"])
router.add_api_route("/email/send-bulk", email.send_bulk_notification, methods=["POST"], tags=["Email"])

# Aadhaar KYC mapping
router.add_api_route("/aadhaar/upload", aadhaar.upload_aadhaar, methods=["POST"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/", aadhaar.list_aadhaar, methods=["GET"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/{doc_id}", aadhaar.get_aadhaar, methods=["GET"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/{doc_id}/image", aadhaar.get_aadhaar_image, methods=["GET"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/{doc_id}/link", aadhaar.link_aadhaar, methods=["POST"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/{doc_id}/approve", aadhaar.approve_aadhaar, methods=["POST"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/{doc_id}/reject", aadhaar.reject_aadhaar, methods=["POST"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/{doc_id}/defer", aadhaar.defer_aadhaar, methods=["POST"], tags=["Aadhaar"])
router.add_api_route("/aadhaar/{doc_id}/unlink", aadhaar.unlink_aadhaar, methods=["POST"], tags=["Aadhaar"])

# PDF Downloads
router.add_api_route("/pdf/receipt/{entry_id}", pdf_exports.receipt_pdf, methods=["GET"], tags=["PDF"])
router.add_api_route("/pdf/passbook/{member_id}", pdf_exports.passbook_pdf, methods=["GET"], tags=["PDF"])
router.add_api_route("/pdf/loan-schedule/{loan_id}", pdf_exports.loan_schedule_pdf, methods=["GET"], tags=["PDF"])
router.add_api_route("/pdf/profit-loss", pdf_exports.pnl_pdf, methods=["GET"], tags=["PDF"])
router.add_api_route("/pdf/balance-sheet", pdf_exports.balance_sheet_pdf, methods=["GET"], tags=["PDF"])
