"""add transaction_id to share_transactions

Revision ID: a3c4d5e6f7a8
Revises: f2b3c4d5e6f7
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa


revision = "a3c4d5e6f7a8"
down_revision = "f2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("share_transactions", sa.Column("transaction_id", sa.String(length=40), nullable=True))
    # Backfill existing rows with unique references.
    op.execute(
        "UPDATE share_transactions "
        "SET transaction_id = 'SHTXN-' || upper(substr(md5(random()::text || id::text), 1, 10)) "
        "WHERE transaction_id IS NULL"
    )
    op.alter_column("share_transactions", "transaction_id", nullable=False)
    op.create_unique_constraint("uq_share_txn_transaction_id", "share_transactions", ["transaction_id"])
    op.create_index("ix_share_transactions_transaction_id", "share_transactions", ["transaction_id"])


def downgrade():
    op.drop_index("ix_share_transactions_transaction_id", table_name="share_transactions")
    op.drop_constraint("uq_share_txn_transaction_id", "share_transactions", type_="unique")
    op.drop_column("share_transactions", "transaction_id")
