"""legacy transaction import schema: loan_transactions + share txn voucher/month

Revision ID: b4d5e6f7a8b9
Revises: a3c4d5e6f7a8
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa


revision = "b4d5e6f7a8b9"
down_revision = "a3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade():
    # --- share_transactions: add reference_month + voucher_no, dedup constraint ---
    op.add_column("share_transactions", sa.Column("reference_month", sa.Date(), nullable=True))
    op.add_column("share_transactions", sa.Column("voucher_no", sa.String(length=40), nullable=True))
    op.create_index("ix_share_transactions_voucher_no", "share_transactions", ["voucher_no"])
    op.create_unique_constraint("uq_share_txn_member_voucher", "share_transactions", ["member_id", "voucher_no"])

    # --- loan_transactions: new append-only table ---
    op.create_table(
        "loan_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.String(length=40), nullable=False),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("loan_id", sa.Integer(), sa.ForeignKey("loan_accounts.id"), nullable=True),
        sa.Column("txn_type", sa.String(length=40), nullable=False, server_default="loan_repayment"),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("txn_date", sa.Date(), nullable=False),
        sa.Column("reference_month", sa.Date(), nullable=True),
        sa.Column("voucher_no", sa.String(length=40), nullable=True),
        sa.Column("journal_entry_id", sa.Integer(), sa.ForeignKey("journal_entries.id"), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("amount >= 0", name="ck_loan_txn_amount_non_neg"),
        sa.UniqueConstraint("transaction_id", name="uq_loan_txn_transaction_id"),
        sa.UniqueConstraint("member_id", "voucher_no", name="uq_loan_txn_member_voucher"),
    )
    op.create_index("ix_loan_transactions_member_id", "loan_transactions", ["member_id"])
    op.create_index("ix_loan_transactions_loan_id", "loan_transactions", ["loan_id"])
    op.create_index("ix_loan_transactions_voucher_no", "loan_transactions", ["voucher_no"])
    op.create_index("ix_loan_transactions_transaction_id", "loan_transactions", ["transaction_id"])


def downgrade():
    op.drop_table("loan_transactions")
    op.drop_constraint("uq_share_txn_member_voucher", "share_transactions", type_="unique")
    op.drop_index("ix_share_transactions_voucher_no", table_name="share_transactions")
    op.drop_column("share_transactions", "voucher_no")
    op.drop_column("share_transactions", "reference_month")
