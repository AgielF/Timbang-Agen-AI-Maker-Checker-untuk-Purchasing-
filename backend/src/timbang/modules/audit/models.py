"""SQLAlchemy 2.0 models for the audit module.

TODO (next session):
- Add transaction amount, currency, PO number fields to AuditFinding
- Add checked_by (user FK), notes fields to CheckResult
- Add composite indexes for severity + created_at queries
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timbang.shared.db.base import Base


class AuditFinding(Base):
    """An audit finding raised by the Checker Agent."""

    __tablename__ = "audit_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transaction_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # low | medium | high | critical
    description: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # TODO: add po_number, amount, currency, sop_reference
    check_results: Mapped[list[CheckResult]] = relationship(back_populates="finding")


class CheckResult(Base):
    """Result of a three-way matching / SOP validation check."""

    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | approved | rejected
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # TODO: add checked_by (FK to users), notes, evidence_url
    finding: Mapped[AuditFinding] = relationship(back_populates="check_results")
