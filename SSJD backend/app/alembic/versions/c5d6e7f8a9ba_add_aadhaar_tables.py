"""add aadhaar document + audit tables

Revision ID: c5d6e7f8a9ba
Revises: b4d5e6f7a8b9
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa


revision = "c5d6e7f8a9ba"
down_revision = "b4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "aadhaar_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("confirmed_name", sa.String(length=160), nullable=False),
        sa.Column("aadhaar_hash", sa.String(length=64), nullable=True),
        sa.Column("aadhaar_last4", sa.String(length=4), nullable=True),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("image_path", sa.String(length=255), nullable=True),
        sa.Column("image_mime", sa.String(length=80), nullable=True),
        sa.Column("match_confidence", sa.String(length=20), nullable=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id"), nullable=True),
        sa.Column("link_basis", sa.Text(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=True),
        sa.Column("decided_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.UniqueConstraint("aadhaar_hash", name="uq_aadhaar_hash"),
        sa.UniqueConstraint("member_id", name="uq_aadhaar_member"),
    )
    op.create_index("ix_aadhaar_documents_status", "aadhaar_documents", ["status"])
    op.create_index("ix_aadhaar_documents_hash", "aadhaar_documents", ["aadhaar_hash"])

    op.create_table(
        "aadhaar_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("aadhaar_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("actor", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_aadhaar_audit_document", "aadhaar_audit_log", ["document_id"])


def downgrade():
    op.drop_table("aadhaar_audit_log")
    op.drop_table("aadhaar_documents")
