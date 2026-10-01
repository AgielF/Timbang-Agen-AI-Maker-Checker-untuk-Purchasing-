"""Procurement router — HTTP boundary.

Rules (docs/agents/BACKEND_AGENTS.md):
- Router delegates to service, never calls repository directly.
- Request/response validated by Pydantic schemas.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from timbang.modules.procurement.repository import PriceQuoteRepository, VendorRepository
from timbang.modules.procurement.schemas import RecommendationResponse, VendorRead
from timbang.modules.procurement.service import ProcurementService
from timbang.shared.db.session import get_session

router = APIRouter(tags=["procurement"])


def _build_service(session: AsyncSession = Depends(get_session)) -> ProcurementService:
    return ProcurementService(
        vendor_repo=VendorRepository(session),
        quote_repo=PriceQuoteRepository(session),
    )


@router.get("/vendors", response_model=list[VendorRead])
async def list_vendors(
    limit: int = 50,
    service: ProcurementService = Depends(_build_service),
) -> list[VendorRead]:
    """List all vendors."""
    return await service.list_vendors(limit=limit)


@router.get("/recommendation", response_model=RecommendationResponse)
async def get_recommendation(
    item_name: str,
    service: ProcurementService = Depends(_build_service),
) -> RecommendationResponse:
    """Get Maker Agent recommendation for an item (stub)."""
    try:
        return await service.get_recommendation(item_name=item_name)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
