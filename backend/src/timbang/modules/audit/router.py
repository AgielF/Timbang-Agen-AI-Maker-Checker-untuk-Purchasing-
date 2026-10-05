"""Audit router — HTTP boundary.

Rules (docs/agents/BACKEND_AGENTS.md):
- Router delegates to service, never calls repository directly.
- Domain exceptions mapped to HTTP status codes here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
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
from timbang.shared.core.middleware import limiter
from timbang.shared.db.session import get_session

router = APIRouter(tags=["audit"])


def _map_exception(exc: DomainError) -> HTTPException:
    """Map an audit domain error to the existing client-error response shape."""
    return HTTPException(status_code=400, detail=str(exc))


def _build_service(session: AsyncSession = Depends(get_session)) -> AuditService:
    return AuditService(
        finding_repo=AuditFindingRepository(session),
        check_repo=CheckResultRepository(session),
    )


class ThreeWayMatchBody(BaseModel):
    po: DocumentData
    gr: DocumentData
    invoice: DocumentData


class RiskReportBody(BaseModel):
    po: DocumentData | None = None
    gr: DocumentData | None = None
    invoice: DocumentData | None = None
    has_level2_approval: bool = False
    has_complete_docs: bool = True


@router.post("/findings", response_model=AuditFindingRead, status_code=201)
@limiter.limit("60/minute")
async def create_finding(
    request: Request,
    data: AuditFindingCreate,
    service: AuditService = Depends(_build_service),
) -> AuditFindingRead:
    """Create a new audit finding."""
    return await service.create_finding(data)


@router.get("/findings/{finding_id}", response_model=AuditFindingRead)
@limiter.limit("120/minute")
async def get_finding(
    request: Request,
    finding_id: uuid.UUID,
    service: AuditService = Depends(_build_service),
) -> AuditFindingRead:
    """Retrieve a single audit finding."""
    result = await service.get_finding(str(finding_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found.")
    return result


@router.post("/transactions/{transaction_id}/match")
@limiter.limit("60/minute")
async def three_way_match(
    request: Request,
    transaction_id: str,
    body: ThreeWayMatchBody,
    service: AuditService = Depends(_build_service),
) -> dict:
    """Perform three-way matching for a transaction."""
    result = service.three_way_matching(po_data=body.po, gr_data=body.gr, invoice_data=body.invoice)
    return result.model_dump()


@router.post("/transactions/{transaction_id}/risk-report", response_model=RiskReportResponse)
@limiter.limit("10/minute")
async def generate_risk_report(
    request: Request,
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
        raise _map_exception(exc) from exc


@router.post(
    "/transactions/{tx_id}/risk-report-with-files",
    response_model=RiskReportResponse,
)
@limiter.limit("5/minute")
async def risk_report_with_files(
    request: Request,
    tx_id: str,
    po_file: UploadFile = File(...),
    gr_file: UploadFile = File(...),
    invoice_file: UploadFile = File(...),
    tax_invoice_file: UploadFile | None = File(None),
    has_level2_approval: bool = Form(False),
    has_complete_docs: bool = Form(True),
    service: AuditService = Depends(_build_service),
) -> RiskReportResponse:
    """Extract uploaded procurement PDFs and generate their Checker report."""
    try:
        return await service.get_risk_report_from_files(
            tx_id=tx_id,
            po_file=po_file,
            gr_file=gr_file,
            invoice_file=invoice_file,
            tax_invoice_file=tax_invoice_file,
            has_level2_approval=has_level2_approval,
            has_complete_docs=has_complete_docs,
        )
    except DomainError as exc:
        raise _map_exception(exc) from exc
