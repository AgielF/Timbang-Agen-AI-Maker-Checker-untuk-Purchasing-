"""Pydantic v2 schemas for the procurement module.

Separate request/response models enforce OWASP API3
(Broken Object Property Level Authorization).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, HttpUrl

# ── Vendor ──────────────────────────────────────────────────────────────────


class VendorCreate(BaseModel):
    name: str
    contact_email: str | None = None
    phone: str | None = None
    address: str | None = None


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    contact_email: str | None
    phone: str | None
    address: str | None
    is_active: bool
    created_at: datetime


# ── PriceQuote ───────────────────────────────────────────────────────────────


class PriceQuoteCreate(BaseModel):
    vendor_id: uuid.UUID
    item_name: str
    quantity: Decimal = Decimal("1")
    unit: str | None = None
    price: Decimal
    currency: str = "IDR"
    source_url: str | None = None
    valid_until: datetime | None = None
    notes: str | None = None


class PriceQuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: uuid.UUID
    item_name: str
    quantity: Decimal
    unit: str | None
    price: Decimal
    currency: str
    source_url: str | None
    valid_until: datetime | None
    notes: str | None
    created_at: datetime


# ── Cross-validation ─────────────────────────────────────────────────────────


class PriceValidationResult(BaseModel):
    median: Decimal
    min: Decimal
    max: Decimal
    flagged_vendor_ids: list[uuid.UUID]
    spread_percent: Decimal


# ── Recommendation ───────────────────────────────────────────────────────────


class RecommendationResponse(BaseModel):
    """Output of the Maker Agent recommendation flow."""

    vendor_id: uuid.UUID | None = None
    vendor_name: str = ""
    reason: str = ""
    estimated_saving: Decimal = Decimal("0")
    citations: list[HttpUrl] = []
