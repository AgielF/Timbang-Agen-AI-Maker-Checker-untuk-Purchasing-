"""SQLAlchemy 2.0 models for the procurement module.

TODO (next session):
- Add category, lead_time, is_active fields to Vendor
- Add quantity, unit fields to PriceQuote
- Add composite indexes for common query patterns
- Add __repr__ methods
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timbang.shared.db.base import Base


class Vendor(Base):
    """Represents a vendor/supplier in the procurement context."""

    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # TODO: add contact_email, phone, address, is_active
    quotes: Mapped[list[PriceQuote]] = relationship(back_populates="vendor")


class PriceQuote(Base):
    """Price quotation from a vendor for a specific item."""

    __tablename__ = "price_quotes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="IDR", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # TODO: add quantity, unit, valid_until, notes
    vendor: Mapped[Vendor] = relationship(back_populates="quotes")
