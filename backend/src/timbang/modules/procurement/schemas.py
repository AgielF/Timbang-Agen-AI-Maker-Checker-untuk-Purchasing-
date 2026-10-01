"""Pydantic v2 schemas for the procurement module.

Separate request/response models enforce OWASP API3
(Broken Object Property Level Authorization).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ── Vendor ──────────────────────────────────────────────────────────────────

class VendorCreate(BaseModel):
    name: str


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


# ── PriceQuote ───────────────────────────────────────────────────────────────

class PriceQuoteCreate(BaseModel):
    vendor_id: uuid.UUID
    item_name: str
    price: Decimal
    currency: str = "IDR"
    source_url: str | None = None


class PriceQuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: uuid.UUID
    item_name: str
    price: Decimal
    currency: str
    source_url: str | None
    created_at: datetime


# ── Recommendation ───────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """Output of the Maker Agent recommendation flow."""

    # TODO (next session): populate from LLM / Langflow output
    recommended_vendor_id: uuid.UUID | None = None
    estimated_savings: Decimal | None = None
    rationale: str = ""
