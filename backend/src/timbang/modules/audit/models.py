"""SQLAlchemy 2.0 models for the audit module."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timbang.shared.db.base import Base


class AuditFinding(Base):
    """An audit finding raised by the Checker Agent."""

    __tablename__ = "audit_findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MEDIUM"
    )  # LOW | MEDIUM | HIGH | CRITICAL
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="IDR")
    description: Mapped[str] = mapped_column(String(2048), nullable=False)
    sop_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    sop_clause_citation: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    check_results: Mapped[list[CheckResult]] = relationship(back_populates="finding")


class CheckResult(Base):
    """Result of a three-way matching / SOP validation check."""

    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit_findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="PASS"
    )  # PASS | FAIL | WARN
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    evidence_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    finding: Mapped[AuditFinding] = relationship(back_populates="check_results")
