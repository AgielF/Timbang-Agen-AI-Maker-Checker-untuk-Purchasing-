"""Procurement repository — the ONLY layer that uses AsyncSession.

Dependency Rule: repository ← service ← router.
No other module layer may import AsyncSession or call DB directly.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from timbang.modules.procurement.models import PriceQuote, Vendor
from timbang.modules.procurement.schemas import PriceQuoteCreate, VendorCreate


class VendorRepository:
    """Data access layer for Vendor entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> Vendor | None:
        result = await self._session.execute(select(Vendor).where(Vendor.id == id))
        return result.scalar_one_or_none()

    async def create(self, data: VendorCreate) -> Vendor:
        vendor = Vendor(name=data.name)
        self._session.add(vendor)
        await self._session.commit()
        await self._session.refresh(vendor)
        return vendor

    async def list(self, limit: int = 50) -> list[Vendor]:
        result = await self._session.execute(select(Vendor).limit(limit))
        return list(result.scalars().all())


class PriceQuoteRepository:
    """Data access layer for PriceQuote entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> PriceQuote | None:
        result = await self._session.execute(select(PriceQuote).where(PriceQuote.id == id))
        return result.scalar_one_or_none()

    async def create(self, data: PriceQuoteCreate) -> PriceQuote:
        quote = PriceQuote(**data.model_dump())
        self._session.add(quote)
        await self._session.commit()
        await self._session.refresh(quote)
        return quote

    async def list(self, limit: int = 50) -> list[PriceQuote]:
        result = await self._session.execute(select(PriceQuote).limit(limit))
        return list(result.scalars().all())
