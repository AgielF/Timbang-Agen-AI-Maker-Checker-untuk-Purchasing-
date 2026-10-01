"""Audit router — HTTP boundary.

Rules (docs/agents/BACKEND_AGENTS.md):
- Router delegates to service, never calls repository directly.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import AuditFindingRead, RiskReportResponse
from timbang.modules.audit.service import AuditService
from timbang.shared.db.session import get_session

router = APIRouter(tags=["audit"])


def _build_service(session: AsyncSession = Depends(get_session)) -> AuditService:
    return AuditService(
        finding_repo=AuditFindingRepository(session),
        check_repo=CheckResultRepository(session),
    )


@router.get("/findings", response_model=list[AuditFindingRead])
async def list_findings(
    limit: int = 50,
    service: AuditService = Depends(_build_service),
) -> list[AuditFindingRead]:
    """List all audit findings."""
    return await service.list_findings(limit=limit)


@router.get("/risk-report", response_model=RiskReportResponse)
async def get_risk_report(
    transaction_id: str,
    service: AuditService = Depends(_build_service),
) -> RiskReportResponse:
    """Get Checker Agent risk report for a transaction (stub)."""
    try:
        return await service.generate_risk_report(transaction_id=transaction_id)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
