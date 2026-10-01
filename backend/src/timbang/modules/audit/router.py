"""Audit router — HTTP boundary.

Rules (docs/agents/BACKEND_AGENTS.md):
- Router delegates to service, never calls repository directly.
- Domain exceptions mapped to HTTP status codes here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import (
    AuditFindingCreate,
    AuditFindingRead,
    DocumentData,
    RiskReportResponse,
)
from timbang.modules.audit.service import AuditService
from timbang.shared.core.exceptions import DomainError
from timbang.shared.db.session import get_session

router = APIRouter(tags=["audit"])


def _build_service(session: AsyncSession = Depends(get_session)) -> AuditService:
    return AuditService(
        finding_repo=AuditFindingRepository(session),
        check_repo=CheckResultRepository(session),
    )


class ThreeWayMatchRequest(DocumentData):
    """Wrapper to accept po/gr/invoice in one request body."""

    pass


class RiskReportRequest(DocumentData):
    has_level2_approval: bool = False
    has_complete_docs: bool = True


@router.post("/findings", response_model=AuditFindingRead, status_code=201)
async def create_finding(
    data: AuditFindingCreate,
    service: AuditService = Depends(_build_service),
) -> AuditFindingRead:
    """Create a new audit finding."""
    return await service.create_finding(data)


@router.get("/findings/{finding_id}", response_model=AuditFindingRead)
async def get_finding(
    finding_id: uuid.UUID,
    service: AuditService = Depends(_build_service),
) -> AuditFindingRead:
    """Retrieve a single audit finding."""
    result = await service.get_finding(str(finding_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found.")
    return result


class MatchRequestBody(DocumentData):
    pass


from pydantic import BaseModel  # noqa: E402


class ThreeWayMatchBody(BaseModel):
    po: DocumentData
    gr: DocumentData
    invoice: DocumentData


@router.post("/transactions/{transaction_id}/match")
async def three_way_match(
    transaction_id: str,
    body: ThreeWayMatchBody,
    service: AuditService = Depends(_build_service),
) -> dict:
    """Perform three-way matching for a transaction."""
    result = service.three_way_matching(po_data=body.po, gr_data=body.gr, invoice_data=body.invoice)
    return result.model_dump()


class RiskReportBody(BaseModel):
    po: DocumentData | None = None
    gr: DocumentData | None = None
    invoice: DocumentData | None = None
    has_level2_approval: bool = False
    has_complete_docs: bool = True


@router.post("/transactions/{transaction_id}/risk-report", response_model=RiskReportResponse)
async def generate_risk_report(
    transaction_id: str,
    body: RiskReportBody,
    service: AuditService = Depends(_build_service),
) -> RiskReportResponse:
    """Generate a risk report for a transaction."""
    try:
        return await service.generate_risk_report(
            transaction_id=transaction_id,
            po_data=body.po,
            gr_data=body.gr,
            invoice_data=body.invoice,
            has_level2_approval=body.has_level2_approval,
            has_complete_docs=body.has_complete_docs,
        )
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
