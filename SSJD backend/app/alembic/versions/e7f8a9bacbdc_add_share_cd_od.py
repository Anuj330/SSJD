"""add CD/OD split to share money

Revision ID: e7f8a9bacbdc
Revises: d6e7f8a9bacb
Create Date: 2026-07-04

"""
from alembic import op
import sqlalchemy as sa


revision = "e7f8a9bacbdc"
down_revision = "d6e7f8a9bacb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("share_holdings", sa.Column("cd_balance", sa.Numeric(14, 2), nullable=False, server_default="0"))
    op.add_column("share_holdings", sa.Column("od_balance", sa.Numeric(14, 2), nullable=False, server_default="0"))
    op.add_column("share_transactions", sa.Column("cd_amount", sa.Numeric(14, 2), nullable=False, server_default="0"))
    op.add_column("share_transactions", sa.Column("od_amount", sa.Numeric(14, 2), nullable=False, server_default="0"))
    # Existing deposits: treat the whole amount as Compulsory Deposit (best-effort backfill).
    op.execute("UPDATE share_transactions SET cd_amount = amount WHERE txn_type = 'monthly_share_deposit'")
    op.execute("UPDATE share_holdings SET cd_balance = balance")


def downgrade():
    op.drop_column("share_transactions", "od_amount")
    op.drop_column("share_transactions", "cd_amount")
    op.drop_column("share_holdings", "od_balance")
    op.drop_column("share_holdings", "cd_balance")
