"""simplify share money to a plain money account

Revision ID: f2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-06-21

- share_holdings: total_value -> balance; drop total_shares, face_value_per_share
- share_transactions: txn_type enum -> varchar; map old values; drop shares column
"""
from alembic import op
import sqlalchemy as sa


revision = "f2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    # --- share_holdings: become a single balance ---
    op.drop_constraint("ck_share_total_non_neg", "share_holdings", type_="check")
    op.alter_column("share_holdings", "total_value", new_column_name="balance")
    op.drop_column("share_holdings", "total_shares")
    op.drop_column("share_holdings", "face_value_per_share")
    op.create_check_constraint("ck_share_balance_non_neg", "share_holdings", "balance >= 0")

    # --- share_transactions: txn_type enum -> string, map old values, drop shares ---
    op.alter_column(
        "share_transactions", "txn_type",
        existing_type=sa.Enum("purchase", "transfer", "refund", "dividend", name="share_txn_type_enum"),
        type_=sa.String(length=40),
        existing_nullable=False,
        postgresql_using="txn_type::text",
    )
    op.execute("UPDATE share_transactions SET txn_type = 'monthly_share_deposit' WHERE txn_type IN ('purchase', 'transfer')")
    op.execute("UPDATE share_transactions SET txn_type = 'withdrawal' WHERE txn_type = 'refund'")
    op.drop_column("share_transactions", "shares")
    op.execute("DROP TYPE IF EXISTS share_txn_type_enum")


def downgrade():
    # Best-effort reverse (share/face-value detail is not recoverable).
    share_enum = sa.Enum("purchase", "transfer", "refund", "dividend", name="share_txn_type_enum")
    share_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("share_transactions", sa.Column("shares", sa.Integer(), nullable=False, server_default="0"))
    op.execute("UPDATE share_transactions SET txn_type = 'purchase' WHERE txn_type = 'monthly_share_deposit'")
    op.execute("UPDATE share_transactions SET txn_type = 'refund' WHERE txn_type = 'withdrawal'")
    op.alter_column(
        "share_transactions", "txn_type",
        type_=share_enum,
        existing_type=sa.String(length=40),
        existing_nullable=False,
        postgresql_using="txn_type::share_txn_type_enum",
    )
    op.drop_constraint("ck_share_balance_non_neg", "share_holdings", type_="check")
    op.add_column("share_holdings", sa.Column("face_value_per_share", sa.Numeric(14, 2), nullable=False, server_default="10"))
    op.add_column("share_holdings", sa.Column("total_shares", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("share_holdings", "balance", new_column_name="total_value")
    op.create_check_constraint("ck_share_total_non_neg", "share_holdings", "total_shares >= 0")
