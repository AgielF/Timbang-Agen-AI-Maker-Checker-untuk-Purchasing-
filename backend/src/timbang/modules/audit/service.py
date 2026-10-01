"""Audit service — business logic layer.

Rules (docs/agents/BACKEND_AGENTS.md):
- Does NOT import AsyncSession — only repository interfaces.
- Orchestrates three-way matching and SOP validation (stub for now).
"""

from __future__ import annotations

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import AuditFindingRead, RiskReportResponse


class AuditService:
    """Business logic for the Checker Agent audit context."""

    def __init__(
        self,
        finding_repo: AuditFindingRepository,
        check_repo: CheckResultRepository,
    ) -> None:
        self._finding_repo = finding_repo
        self._check_repo = check_repo

    async def list_findings(self, limit: int = 50) -> list[AuditFindingRead]:
        """Return a list of audit findings."""
        findings = await self._finding_repo.list(limit=limit)
        return [AuditFindingRead.model_validate(f) for f in findings]

    async def generate_risk_report(self, transaction_id: str) -> RiskReportResponse:
        """Generate a risk report for a transaction.

        TODO (next session): implement three-way matching (PO / GR / Invoice),
        SOP validation, and integrate with Langflow Checker Agent flow.
        """
        raise NotImplementedError("TODO next session — three-way matching pending")
