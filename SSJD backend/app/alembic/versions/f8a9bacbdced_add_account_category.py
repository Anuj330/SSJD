"""add category to ledger accounts (P&L bifurcation heads)

Revision ID: f8a9bacbdced
Revises: e7f8a9bacbdc
Create Date: 2026-07-04

"""
from alembic import op
import sqlalchemy as sa


revision = "f8a9bacbdced"
down_revision = "e7f8a9bacbdc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("accounts", sa.Column("category", sa.String(80), nullable=True))


def downgrade():
    op.drop_column("accounts", "category")
