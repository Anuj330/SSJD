"""Aadhaar document intake + name-matching workflow.

PII handling: the full 12-digit Aadhaar number is NEVER stored. We keep a one-way
hash (for de-duplication) and the last 4 digits (for display). The card image is
stored on a restricted volume and only served through an admin-auth endpoint.
"""

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from .base import TimestampMixin

# Workflow states
AADHAAR_PENDING = "pending"            # uploaded, awaiting review
AADHAAR_PENDING_APPROVAL = "pending_approval"  # linked by operator, needs checker (ambiguous/fuzzy)
AADHAAR_LINKED = "linked"              # confirmed link to a member
AADHAAR_NEEDS_INFO = "needs_info"      # deferred — more verification required
AADHAAR_REJECTED = "rejected"          # wrong / illegible / not ours


class AadhaarDocument(Base, TimestampMixin):
    __tablename__ = "aadhaar_documents"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default=AADHAAR_PENDING, index=True)

    # From the card (operator-confirmed)
    confirmed_name = Column(String(160), nullable=False)
    aadhaar_hash = Column(String(64), nullable=True, unique=True, index=True)  # sha256 of full number
    aadhaar_last4 = Column(String(4), nullable=True)
    dob = Column(Date, nullable=True)

    # Stored image (restricted)
    image_path = Column(String(255), nullable=True)
    image_mime = Column(String(80), nullable=True)

    # Matching outcome at intake
    match_confidence = Column(String(20), nullable=True)  # high | ambiguous | fuzzy | none

    # Linkage
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True, unique=True)  # one linked Aadhaar per member
    link_basis = Column(Text, nullable=True)   # reviewer's stated basis for the match
    remarks = Column(Text, nullable=True)

    # Who-did-what (maker / checker)
    uploaded_by = Column(Integer, nullable=True)
    decided_by = Column(Integer, nullable=True)   # operator who proposed the link / rejection
    approved_by = Column(Integer, nullable=True)   # checker who confirmed an ambiguous link
    linked_at = Column(DateTime(timezone=True), nullable=True)

    member = relationship("Member")


class AadhaarAuditLog(Base):
    __tablename__ = "aadhaar_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("aadhaar_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(40), nullable=False)
    actor = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
