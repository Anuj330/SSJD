"""PDF generation for receipts, statements, reports using WeasyPrint + Jinja2."""

import io
from datetime import date
from jinja2 import Template


def _fmt(n):
    """Format number as INR."""
    try:
        return f"₹{float(n):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


_BASE_CSS = """
body { font-family: sans-serif; font-size: 12px; color: #333; margin: 20px; }
h1 { font-size: 20px; color: #1a1a1a; border-bottom: 2px solid #2563eb; padding-bottom: 8px; }
h2 { font-size: 16px; color: #1a1a1a; margin-top: 20px; }
.header { text-align: center; margin-bottom: 20px; }
.header h1 { border: none; }
.header p { color: #666; font-size: 11px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th { background: #f3f4f6; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb; }
td { padding: 6px 8px; border-bottom: 1px solid #e5e7eb; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.total-row { font-weight: bold; background: #f9fafb; }
.amount-green { color: #059669; }
.amount-red { color: #dc2626; }
.amount-blue { color: #2563eb; }
.meta { display: flex; justify-content: space-between; margin-bottom: 15px; padding: 10px; background: #f9fafb; border-radius: 6px; }
.meta-item { }
.meta-label { font-size: 10px; color: #666; text-transform: uppercase; }
.meta-value { font-size: 14px; font-weight: bold; }
.footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #e5e7eb; text-align: center; color: #999; font-size: 10px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 10px; font-weight: 600; }
.badge-green { background: #d1fae5; color: #065f46; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-yellow { background: #fef3c7; color: #92400e; }
"""

_RECEIPT_TEMPLATE = Template("""
<html><head><style>{{ css }}</style></head><body>
<div class="header">
  <h1>SSJD Cooperative Society</h1>
  <p>Shramik Sahkari Jaivik Darshan</p>
</div>
<h2>Transaction Receipt</h2>
<div class="meta">
  <div class="meta-item"><div class="meta-label">Txn Ref</div><div class="meta-value">{{ entry.txn_ref }}</div></div>
  <div class="meta-item"><div class="meta-label">Type</div><div class="meta-value">{{ entry.txn_type }}</div></div>
  <div class="meta-item"><div class="meta-label">Date</div><div class="meta-value">{{ entry.created_at }}</div></div>
  <div class="meta-item"><div class="meta-label">Status</div><div class="meta-value">{{ entry.status }}</div></div>
</div>
<p><strong>Description:</strong> {{ entry.description }}</p>
<table>
  <thead><tr><th>Account</th><th>Code</th><th class="text-right">Debit</th><th class="text-right">Credit</th></tr></thead>
  <tbody>
  {% for line in lines %}
  <tr>
    <td>{{ line.account_name }}</td><td>{{ line.account_code }}</td>
    <td class="text-right">{{ line.dr_display }}</td>
    <td class="text-right">{{ line.cr_display }}</td>
  </tr>
  {% endfor %}
  <tr class="total-row"><td colspan="2">Total</td><td class="text-right">{{ total_dr }}</td><td class="text-right">{{ total_cr }}</td></tr>
  </tbody>
</table>
<div class="footer">Generated on {{ today }} | SSJD Cooperative Society</div>
</body></html>
""")

_PASSBOOK_TEMPLATE = Template("""
<html><head><style>{{ css }}</style></head><body>
<div class="header">
  <h1>SSJD Cooperative Society</h1>
  <p>Member Passbook Statement</p>
</div>
<div class="meta">
  <div class="meta-item"><div class="meta-label">Member</div><div class="meta-value">{{ member_name }} (#{{ member_id }})</div></div>
  <div class="meta-item"><div class="meta-label">Period</div><div class="meta-value">{{ from_date }} to {{ to_date }}</div></div>
  <div class="meta-item"><div class="meta-label">Balance</div><div class="meta-value amount-green">{{ current_balance }}</div></div>
</div>
<table>
  <thead><tr><th>Date</th><th>Type</th><th>Description</th><th class="text-right">Credit</th><th class="text-right">Debit</th><th class="text-right">Balance</th></tr></thead>
  <tbody>
  {% for row in rows %}
  <tr>
    <td>{{ row.date }}</td><td>{{ row.txn_type }}</td><td>{{ row.description }}</td>
    <td class="text-right amount-green">{{ row.credit }}</td>
    <td class="text-right amount-red">{{ row.debit }}</td>
    <td class="text-right"><strong>{{ row.running_balance }}</strong></td>
  </tr>
  {% endfor %}
  <tr class="total-row"><td colspan="3">Totals</td><td class="text-right amount-green">{{ total_credited }}</td><td class="text-right amount-red">{{ total_debited }}</td><td></td></tr>
  </tbody>
</table>
<div class="footer">Generated on {{ today }} | SSJD Cooperative Society</div>
</body></html>
""")

_LOAN_SCHEDULE_TEMPLATE = Template("""
<html><head><style>{{ css }}</style></head><body>
<div class="header">
  <h1>SSJD Cooperative Society</h1>
  <p>EMI Repayment Schedule</p>
</div>
<div class="meta">
  <div class="meta-item"><div class="meta-label">Loan #</div><div class="meta-value">{{ loan_number }}</div></div>
  <div class="meta-item"><div class="meta-label">Member</div><div class="meta-value">{{ member_name }}</div></div>
  <div class="meta-item"><div class="meta-label">Amount</div><div class="meta-value">{{ disbursed_amount }}</div></div>
  <div class="meta-item"><div class="meta-label">Rate</div><div class="meta-value">{{ interest_rate }}%</div></div>
  <div class="meta-item"><div class="meta-label">Tenure</div><div class="meta-value">{{ tenure }} months</div></div>
</div>
<table>
  <thead><tr><th>#</th><th>Due Date</th><th class="text-right">Principal</th><th class="text-right">Interest</th><th class="text-right">EMI</th><th class="text-right">Paid</th><th class="text-center">Status</th></tr></thead>
  <tbody>
  {% for r in schedule %}
  <tr>
    <td>{{ r.installment_no }}</td><td>{{ r.due_date }}</td>
    <td class="text-right">{{ r.principal_due }}</td>
    <td class="text-right amount-blue">{{ r.interest_due }}</td>
    <td class="text-right"><strong>{{ r.total_due }}</strong></td>
    <td class="text-right">{{ r.total_paid }}</td>
    <td class="text-center">
      {% if r.is_paid %}<span class="badge badge-green">Paid</span>
      {% elif r.is_overdue %}<span class="badge badge-red">Overdue</span>
      {% else %}<span class="badge badge-yellow">Pending</span>{% endif %}
    </td>
  </tr>
  {% endfor %}
  </tbody>
</table>
<div class="footer">Generated on {{ today }} | SSJD Cooperative Society</div>
</body></html>
""")

_REPORT_TEMPLATE = Template("""
<html><head><style>{{ css }}</style></head><body>
<div class="header">
  <h1>SSJD Cooperative Society</h1>
  <p>{{ report_title }}</p>
</div>
{% if period %}<p><strong>Period:</strong> {{ period }}</p>{% endif %}
{{ content }}
<div class="footer">Generated on {{ today }} | SSJD Cooperative Society</div>
</body></html>
""")


def _render_pdf(html_string: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=html_string).write_pdf()


def generate_receipt_pdf(entry_data: dict, lines_data: list) -> bytes:
    total_dr = sum(float(l.get("dr_amount", 0)) for l in lines_data)
    total_cr = sum(float(l.get("cr_amount", 0)) for l in lines_data)
    lines = []
    for l in lines_data:
        lines.append({
            "account_name": l.get("account_name", ""),
            "account_code": l.get("account_code", ""),
            "dr_display": _fmt(l["dr_amount"]) if float(l.get("dr_amount", 0)) > 0 else "-",
            "cr_display": _fmt(l["cr_amount"]) if float(l.get("cr_amount", 0)) > 0 else "-",
        })
    html = _RECEIPT_TEMPLATE.render(
        css=_BASE_CSS, entry=entry_data, lines=lines,
        total_dr=_fmt(total_dr), total_cr=_fmt(total_cr),
        today=date.today().isoformat(),
    )
    return _render_pdf(html)


def generate_passbook_pdf(member_name: str, member_id: int, rows: list,
                          summary: dict, from_date=None, to_date=None) -> bytes:
    fmt_rows = []
    for r in rows:
        fmt_rows.append({
            "date": r.get("date", ""),
            "txn_type": r.get("txn_type", ""),
            "description": r.get("description", "")[:60],
            "credit": _fmt(r["credit"]) if float(r.get("credit", 0)) > 0 else "-",
            "debit": _fmt(r["debit"]) if float(r.get("debit", 0)) > 0 else "-",
            "running_balance": _fmt(r.get("running_balance", 0)),
        })
    html = _PASSBOOK_TEMPLATE.render(
        css=_BASE_CSS, member_name=member_name, member_id=member_id,
        rows=fmt_rows, from_date=from_date or "Start", to_date=to_date or date.today().isoformat(),
        current_balance=_fmt(summary.get("current_balance", 0)),
        total_credited=_fmt(summary.get("total_credited", 0)),
        total_debited=_fmt(summary.get("total_debited", 0)),
        today=date.today().isoformat(),
    )
    return _render_pdf(html)


def generate_loan_schedule_pdf(loan_data: dict, schedule: list) -> bytes:
    fmt_schedule = []
    for r in schedule:
        fmt_schedule.append({
            "installment_no": r["installment_no"],
            "due_date": r.get("due_date", ""),
            "principal_due": _fmt(r.get("principal_due", 0)),
            "interest_due": _fmt(r.get("interest_due", 0)),
            "total_due": _fmt(r.get("total_due", 0)),
            "total_paid": _fmt(r.get("total_paid", 0)) if float(r.get("total_paid", 0)) > 0 else "-",
            "is_paid": r.get("is_paid", False),
            "is_overdue": r.get("is_overdue", False),
        })
    html = _LOAN_SCHEDULE_TEMPLATE.render(
        css=_BASE_CSS, loan_number=loan_data.get("loan_number", ""),
        member_name=loan_data.get("member_name", ""),
        disbursed_amount=_fmt(loan_data.get("disbursed_amount", 0)),
        interest_rate=loan_data.get("interest_rate", 0),
        tenure=loan_data.get("tenure_months", 0),
        schedule=fmt_schedule, today=date.today().isoformat(),
    )
    return _render_pdf(html)


def generate_report_pdf(title: str, content_html: str, period: str = None) -> bytes:
    html = _REPORT_TEMPLATE.render(
        css=_BASE_CSS, report_title=title, content=content_html,
        period=period, today=date.today().isoformat(),
    )
    return _render_pdf(html)


def generate_pnl_pdf(data: dict) -> bytes:
    rows_html = '<h2>Income</h2><table><thead><tr><th>Account</th><th class="text-right">Amount</th></tr></thead><tbody>'
    for r in data.get("income", []):
        rows_html += f'<tr><td>{r["name"]}</td><td class="text-right amount-green">{_fmt(r["amount"])}</td></tr>'
    rows_html += f'<tr class="total-row"><td>Total Income</td><td class="text-right amount-green">{_fmt(data.get("total_income", 0))}</td></tr>'
    rows_html += '</tbody></table>'

    rows_html += '<h2>Expenses</h2><table><thead><tr><th>Account</th><th class="text-right">Amount</th></tr></thead><tbody>'
    for r in data.get("expenses", []):
        rows_html += f'<tr><td>{r["name"]}</td><td class="text-right amount-red">{_fmt(r["amount"])}</td></tr>'
    rows_html += f'<tr class="total-row"><td>Total Expenses</td><td class="text-right amount-red">{_fmt(data.get("total_expenses", 0))}</td></tr>'
    rows_html += '</tbody></table>'

    net = float(data.get("net_profit", 0))
    color = "amount-green" if net >= 0 else "amount-red"
    rows_html += f'<h2>Net Profit / Loss: <span class="{color}">{_fmt(net)}</span></h2>'

    period = ""
    if data.get("from_date"):
        period = f'{data["from_date"]} to {data.get("to_date", "present")}'

    return generate_report_pdf("Profit & Loss Statement", rows_html, period)


def generate_balance_sheet_pdf(data: dict) -> bytes:
    sections = [
        ("Assets", data.get("assets", []), data.get("total_assets", 0), "amount-blue"),
        ("Liabilities", data.get("liabilities", []), data.get("total_liabilities", 0), "amount-red"),
        ("Equity", data.get("equity", []), data.get("total_equity", 0), "amount-green"),
    ]
    html = ""
    for title, items, total, color in sections:
        html += f'<h2>{title}</h2><table><thead><tr><th>Account</th><th>Code</th><th class="text-right">Balance</th></tr></thead><tbody>'
        for r in items:
            html += f'<tr><td>{r["name"]}</td><td>{r["code"]}</td><td class="text-right {color}">{_fmt(r["balance"])}</td></tr>'
        html += f'<tr class="total-row"><td colspan="2">Total {title}</td><td class="text-right {color}">{_fmt(total)}</td></tr></tbody></table>'

    balanced = data.get("is_balanced", False)
    badge = '<span class="badge badge-green">Balanced</span>' if balanced else '<span class="badge badge-red">Unbalanced</span>'
    html += f'<p style="margin-top:20px"><strong>Balance Check (A = L + E):</strong> {badge}</p>'

    return generate_report_pdf("Balance Sheet", html,
                               f'As of {data.get("as_of", date.today().isoformat())}')
