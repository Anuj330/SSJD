"""add ledger tables

Revision ID: e4f12a7b8c90
Revises: c1e90ae77e51
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4f12a7b8c90"
down_revision: Union[str, Sequence[str], None] = "c1e90ae77e51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


account_type_enum = sa.Enum("asset", "liability", "income", "expense", "equity", name="account_type_enum")
owner_type_enum = sa.Enum("society", "member", "system", name="owner_type_enum")
entry_status_enum = sa.Enum("posted", "reversed", name="entry_status_enum")


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", account_type_enum, nullable=False),
        sa.Column("owner_type", owner_type_enum, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_accounts_id"), "accounts", ["id"], unique=False)
    op.create_index(op.f("ix_accounts_code"), "accounts", ["code"], unique=True)
    op.create_index(op.f("ix_accounts_owner_id"), "accounts", ["owner_id"], unique=False)

    op.create_table(
        "journal_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("txn_ref", sa.String(length=100), nullable=False),
        sa.Column("txn_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", entry_status_enum, nullable=False),
        sa.Column("reversed_entry_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["reversed_entry_id"], ["journal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_journal_entries_id"), "journal_entries", ["id"], unique=False)
    op.create_index(op.f("ix_journal_entries_txn_ref"), "journal_entries", ["txn_ref"], unique=True)

    op.create_table(
        "journal_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journal_entry_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("dr_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("cr_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("line_note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.CheckConstraint("dr_amount >= 0", name="ck_journal_lines_dr_non_negative"),
        sa.CheckConstraint("cr_amount >= 0", name="ck_journal_lines_cr_non_negative"),
        sa.CheckConstraint(
            "(dr_amount = 0 AND cr_amount > 0) OR (cr_amount = 0 AND dr_amount > 0)",
            name="ck_journal_lines_one_side_only",
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_journal_lines_id"), "journal_lines", ["id"], unique=False)
    op.create_index(op.f("ix_journal_lines_account_id"), "journal_lines", ["account_id"], unique=False)
    op.create_index(op.f("ix_journal_lines_journal_entry_id"), "journal_lines", ["journal_entry_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_journal_lines_journal_entry_id"), table_name="journal_lines")
    op.drop_index(op.f("ix_journal_lines_account_id"), table_name="journal_lines")
    op.drop_index(op.f("ix_journal_lines_id"), table_name="journal_lines")
    op.drop_table("journal_lines")

    op.drop_index(op.f("ix_journal_entries_txn_ref"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_id"), table_name="journal_entries")
    op.drop_table("journal_entries")

    op.drop_index(op.f("ix_accounts_owner_id"), table_name="accounts")
    op.drop_index(op.f("ix_accounts_code"), table_name="accounts")
    op.drop_index(op.f("ix_accounts_id"), table_name="accounts")
    op.drop_table("accounts")

    entry_status_enum.drop(op.get_bind(), checkfirst=True)
    owner_type_enum.drop(op.get_bind(), checkfirst=True)
    account_type_enum.drop(op.get_bind(), checkfirst=True)
