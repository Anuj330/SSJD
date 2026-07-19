"""add member advance wallet

Revision ID: d6e7f8a9bacb
Revises: c5d6e7f8a9ba
Create Date: 2026-07-01

"""
from alembic import op
import sqlalchemy as sa


revision = "d6e7f8a9bacb"
down_revision = "c5d6e7f8a9ba"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "member_advances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("balance >= 0", name="ck_advance_balance_non_neg"),
        sa.UniqueConstraint("member_id", name="uq_member_advance_member"),
    )
    op.create_index("ix_member_advances_member_id", "member_advances", ["member_id"])

    op.create_table(
        "advance_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.String(40), nullable=False),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("txn_type", sa.String(20), nullable=False, server_default="credit"),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("txn_date", sa.Date(), nullable=False),
        sa.Column("reference", sa.String(120), nullable=True),
        sa.Column("journal_entry_id", sa.Integer(), sa.ForeignKey("journal_entries.id"), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("transaction_id", name="uq_advance_txn_id"),
    )
    op.create_index("ix_advance_transactions_transaction_id", "advance_transactions", ["transaction_id"])
    op.create_index("ix_advance_transactions_member_id", "advance_transactions", ["member_id"])


def downgrade():
    op.drop_table("advance_transactions")
    op.drop_table("member_advances")
