"""Procurement service — business logic layer (Maker Agent).

Rules (docs/agents/BACKEND_AGENTS.md):
- Does NOT import AsyncSession — only repository interfaces.
- Orchestrates repository calls and LLM via 9Router.
- NEVER log API keys (docs/SECURITY.md).
"""

from __future__ import annotations

import json
import statistics
import uuid
from decimal import Decimal

import httpx
import structlog

from timbang.modules.procurement.repository import PriceQuoteRepository, VendorRepository
from timbang.modules.procurement.schemas import (
    PriceQuoteCreate,
    PriceQuoteRead,
    PriceValidationResult,
    RecommendationResponse,
    VendorCreate,
    VendorRead,
)
from timbang.shared.core.config import get_settings
from timbang.shared.core.exceptions import (
    DomainError,
    NotFoundError,
    UpstreamError,
    ValidationError,
)

log = structlog.get_logger(__name__)

_OUTLIER_THRESHOLD = Decimal("0.30")  # 30% deviation from median


class ProcurementService:
    """Business logic for the Maker Agent procurement context."""

    def __init__(
        self,
        vendor_repo: VendorRepository,
        quote_repo: PriceQuoteRepository,
    ) -> None:
        self._vendor_repo = vendor_repo
        self._quote_repo = quote_repo

    # ── Vendors ──────────────────────────────────────────────────────────────

    async def list_vendors(self, limit: int = 50) -> list[VendorRead]:
        """Return a list of all vendors."""
        vendors = await self._vendor_repo.list(limit=limit)
        return [VendorRead.model_validate(v) for v in vendors]

    async def register_vendor(self, data: VendorCreate) -> VendorRead:
        """Register a new vendor. Raises ValidationError if name already exists."""
        existing = await self._vendor_repo.get_by_name(data.name)
        if existing is not None:
            raise ValidationError(f"Vendor with name '{data.name}' already exists.")
        vendor = await self._vendor_repo.create(data)
        log.info("vendor_registered", vendor_id=str(vendor.id), name=vendor.name)
        return VendorRead.model_validate(vendor)

    # ── Quotes ───────────────────────────────────────────────────────────────

    async def submit_quote(self, vendor_id: uuid.UUID, data: PriceQuoteCreate) -> PriceQuoteRead:
        """Submit a price quote for a vendor. Raises NotFoundError if vendor missing."""
        vendor = await self._vendor_repo.get(vendor_id)
        if vendor is None:
            raise NotFoundError(f"Vendor {vendor_id} not found.")
        # Ensure vendor_id on data matches path param
        data_dict = data.model_dump()
        data_dict["vendor_id"] = vendor_id
        quote = await self._quote_repo.create(PriceQuoteCreate(**data_dict))
        log.info("quote_submitted", quote_id=str(quote.id), item=quote.item_name)
        return PriceQuoteRead.model_validate(quote)

    # ── Cross-validation ─────────────────────────────────────────────────────

    async def cross_validate_price(
        self, item_name: str, quotes: list[PriceQuoteRead] | None = None
    ) -> PriceValidationResult:
        """Calculate median price and flag outliers.

        Requires at least 2 quotes. Outlier threshold: |price-median|/median > 30%.
        """
        if quotes is None:
            db_quotes = await self._quote_repo.list_by_item(item_name)
            quotes = [PriceQuoteRead.model_validate(q) for q in db_quotes]

        if len(quotes) < 2:
            raise ValidationError(
                f"Cross-validation requires at least 2 quotes for '{item_name}', "
                f"got {len(quotes)}."
            )

        prices = [float(q.price) for q in quotes]
        median_f = statistics.median(prices)
        median = Decimal(str(median_f))
        min_price = Decimal(str(min(prices)))
        max_price = Decimal(str(max(prices)))
        spread = (max_price - min_price) / median * 100 if median else Decimal("0")

        flagged: list[uuid.UUID] = []
        for q in quotes:
            deviation = abs(q.price - median) / median if median else Decimal("0")
            if deviation > _OUTLIER_THRESHOLD:
                flagged.append(q.vendor_id)

        return PriceValidationResult(
            median=median,
            min=min_price,
            max=max_price,
            flagged_vendor_ids=flagged,
            spread_percent=spread.quantize(Decimal("0.01")),
        )

    # ── Recommendation (LLM) ─────────────────────────────────────────────────

    async def get_recommendation(self, item_name: str) -> RecommendationResponse:
        """Call 9Router LLM to recommend the best vendor for an item.

        Raises UpstreamError on timeout or non-200 from 9Router.
        NEVER logs API key.
        """
        settings = get_settings()
        quotes = await self._quote_repo.list_by_item(item_name)
        if not quotes:
            raise DomainError(f"No price quotes found for item '{item_name}'.")

        validation = await self.cross_validate_price(item_name)

        quotes_summary = [
            {
                "vendor_id": str(q.vendor_id),
                "price": str(q.price),
                "currency": q.currency,
                "source_url": q.source_url,
            }
            for q in [PriceQuoteRead.model_validate(q) for q in quotes]
        ]

        prompt = (
            f"Analisis penawaran harga untuk item '{item_name}'.\n"
            f"Data penawaran: {json.dumps(quotes_summary, ensure_ascii=False)}\n"
            f"Median harga: {validation.median}, Spread: {validation.spread_percent}%\n"
            f"Vendor dengan harga outlier: {[str(v) for v in validation.flagged_vendor_ids]}\n\n"
            "Rekomendasikan vendor terbaik. Jawab dalam JSON dengan field: "
            "vendor_id, vendor_name, reason, estimated_saving, citations (list URL)."
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.nine_router_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.nine_router_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "auto",
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                    },
                )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise UpstreamError(f"9Router unreachable: {exc}") from exc

        if resp.status_code != 200:
            raise UpstreamError(
                f"9Router returned HTTP {resp.status_code}. Check upstream configuration."
            )

        try:
            content = resp.json()["choices"][0]["message"]["content"]
            payload = json.loads(content) if isinstance(content, str) else content
            return RecommendationResponse(
                vendor_id=payload.get("vendor_id"),
                vendor_name=payload.get("vendor_name", ""),
                reason=payload.get("reason", ""),
                estimated_saving=Decimal(str(payload.get("estimated_saving", "0"))),
                citations=payload.get("citations", []),
            )
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise UpstreamError(f"Failed to parse 9Router response: {exc}") from exc
