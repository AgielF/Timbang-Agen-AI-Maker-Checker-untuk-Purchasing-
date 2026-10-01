"""Procurement service — business logic layer.

Rules (docs/agents/BACKEND_AGENTS.md):
- Does NOT import AsyncSession — only repository interfaces.
- Orchesstrates calls to repository and (future) LLM via 9Router/Langflow.
"""

from __future__ import annotations

from timbang.modules.procurement.repository import PriceQuoteRepository, VendorRepository
from timbang.modules.procurement.schemas import RecommendationResponse, VendorRead


class ProcurementService:
    """Business logic for the Maker Agent procurement context."""

    def __init__(
        self,
        vendor_repo: VendorRepository,
        quote_repo: PriceQuoteRepository,
    ) -> None:
        self._vendor_repo = vendor_repo
        self._quote_repo = quote_repo

    async def list_vendors(self, limit: int = 50) -> list[VendorRead]:
        """Return a list of vendors (paginated)."""
        vendors = await self._vendor_repo.list(limit=limit)
        return [VendorRead.model_validate(v) for v in vendors]

    async def get_recommendation(self, item_name: str) -> RecommendationResponse:
        """Return vendor recommendation for an item.

        TODO (next session): integrate with Langflow Maker Agent flow
        and 9Router LLM to generate cross-validated price recommendation.
        """
        raise NotImplementedError("TODO next session — LLM integration pending")
