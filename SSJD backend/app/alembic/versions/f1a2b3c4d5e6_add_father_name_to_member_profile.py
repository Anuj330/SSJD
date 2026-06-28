"""add father_name to member_profiles

Revision ID: f1a2b3c4d5e6
Revises: 4d598ee3ac2b
Create Date: 2026-06-20

"""
from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "4d598ee3ac2b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("member_profiles", sa.Column("father_name", sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column("member_profiles", "father_name")
