"""Email notifications via Brevo (SendinBlue) transactional API."""

import os
import logging

logger = logging.getLogger(__name__)

_api_key = os.getenv("BREVO_API_KEY", "")
_sender_email = os.getenv("BREVO_SENDER_EMAIL", "noreply@ssjd.org")
_sender_name = os.getenv("BREVO_SENDER_NAME", "SSJD Cooperative")


def _get_api():
    """Lazy-init Brevo API client."""
    if not _api_key or _api_key == "REPLACE_ME":
        return None
    import sib_api_v3_sdk
    config = sib_api_v3_sdk.Configuration()
    config.api_key["api-key"] = _api_key
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))


def send_email(to_email: str, to_name: str, subject: str, html_body: str) -> bool:
    """Send a transactional email. Returns True on success, False on failure."""
    api = _get_api()
    if not api:
        logger.warning("Brevo API key not configured — skipping email to %s", to_email)
        return False

    import sib_api_v3_sdk
    email = sib_api_v3_sdk.SendSmtpEmail(
        sender={"email": _sender_email, "name": _sender_name},
        to=[{"email": to_email, "name": to_name}],
        subject=subject,
        html_content=html_body,
    )
    try:
        api.send_transac_email(email)
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False


# ── Pre-built notification helpers ──

def notify_deposit_opened(member_email: str, member_name: str, account_number: str, amount, scheme_name: str):
    send_email(member_email, member_name, f"Deposit Account Opened — {account_number}",
        f"""<h2>Dear {member_name},</h2>
        <p>Your <strong>{scheme_name}</strong> deposit account <strong>{account_number}</strong> has been opened with an initial deposit of <strong>₹{amount:,.2f}</strong>.</p>
        <p>You can view your account details in the Member Portal.</p>
        <br><p>— SSJD Cooperative Society</p>""")


def notify_loan_status(member_email: str, member_name: str, loan_number: str, status: str, amount=None):
    status_msg = {
        "approved": f"Your loan <strong>{loan_number}</strong> has been <strong style='color:green'>approved</strong>" + (f" for ₹{amount:,.2f}" if amount else "") + ".",
        "rejected": f"Your loan application <strong>{loan_number}</strong> has been <strong style='color:red'>rejected</strong>.",
        "disbursed": f"Your loan <strong>{loan_number}</strong> has been <strong>disbursed</strong>. Amount of ₹{amount:,.2f} has been credited.",
    }.get(status, f"Your loan {loan_number} status has been updated to {status}.")

    send_email(member_email, member_name, f"Loan {status.title()} — {loan_number}",
        f"""<h2>Dear {member_name},</h2>
        <p>{status_msg}</p>
        <p>Log in to the Member Portal for details.</p>
        <br><p>— SSJD Cooperative Society</p>""")


def notify_repayment_received(member_email: str, member_name: str, loan_number: str, amount, outstanding):
    send_email(member_email, member_name, f"EMI Payment Received — {loan_number}",
        f"""<h2>Dear {member_name},</h2>
        <p>We have received your repayment of <strong>₹{amount:,.2f}</strong> against loan <strong>{loan_number}</strong>.</p>
        <p>Outstanding balance: <strong>₹{outstanding:,.2f}</strong></p>
        <br><p>— SSJD Cooperative Society</p>""")


def notify_emi_reminder(member_email: str, member_name: str, loan_number: str, due_date, emi_amount):
    send_email(member_email, member_name, f"EMI Due Reminder — {loan_number}",
        f"""<h2>Dear {member_name},</h2>
        <p>This is a reminder that your EMI of <strong>₹{emi_amount:,.2f}</strong> for loan <strong>{loan_number}</strong> is due on <strong>{due_date}</strong>.</p>
        <p>Please ensure timely payment to avoid late penalties.</p>
        <br><p>— SSJD Cooperative Society</p>""")


def notify_emi_overdue(member_email: str, member_name: str, loan_number: str, due_date, emi_amount):
    send_email(member_email, member_name, f"OVERDUE: EMI Payment — {loan_number}",
        f"""<h2>Dear {member_name},</h2>
        <p style="color:red"><strong>Your EMI of ₹{emi_amount:,.2f} for loan {loan_number} was due on {due_date} and is now overdue.</strong></p>
        <p>Late penalties may apply. Please make the payment immediately.</p>
        <br><p>— SSJD Cooperative Society</p>""")


def notify_dividend_posted(member_email: str, member_name: str, shares: int, dividend_amount, year: str):
    send_email(member_email, member_name, f"Dividend Credited — FY {year}",
        f"""<h2>Dear {member_name},</h2>
        <p>A dividend of <strong>₹{dividend_amount:,.2f}</strong> has been credited to your account for FY {year}.</p>
        <p>Shares held: <strong>{shares}</strong></p>
        <br><p>— SSJD Cooperative Society</p>""")


def notify_interest_credited(member_email: str, member_name: str, account_number: str, interest_amount, new_balance):
    send_email(member_email, member_name, f"Interest Credited — {account_number}",
        f"""<h2>Dear {member_name},</h2>
        <p>Interest of <strong>₹{interest_amount:,.2f}</strong> has been credited to your deposit account <strong>{account_number}</strong>.</p>
        <p>New balance: <strong>₹{new_balance:,.2f}</strong></p>
        <br><p>— SSJD Cooperative Society</p>""")
