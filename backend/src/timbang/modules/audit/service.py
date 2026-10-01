"""Audit service — business logic layer (Checker Agent).

Rules (docs/agents/BACKEND_AGENTS.md):
- Does NOT import AsyncSession — only repository interfaces.
- Orchestrates three-way matching and SOP validation.
"""

from __future__ import annotations

from decimal import Decimal

import structlog

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import (
    AuditFindingCreate,
    AuditFindingRead,
    CheckResultCreate,
    DocumentData,
    MatchResult,
    RiskReportResponse,
    SopValidationResult,
)

log = structlog.get_logger(__name__)

# SOP thresholds
_SOP_L2_APPROVAL_THRESHOLD = Decimal("100_000_000")  # 100 juta IDR → level 2 approval required


class AuditService:
    """Business logic for the Checker Agent audit context."""

    def __init__(
        self,
        finding_repo: AuditFindingRepository,
        check_repo: CheckResultRepository,
    ) -> None:
        self._finding_repo = finding_repo
        self._check_repo = check_repo

    # ── Findings CRUD ─────────────────────────────────────────────────────────

    async def create_finding(self, data: AuditFindingCreate) -> AuditFindingRead:
        """Create and persist a new audit finding."""
        finding = await self._finding_repo.create(data)
        log.info(
            "audit_finding_created",
            finding_id=str(finding.id),
            transaction_id=finding.transaction_id,
            severity=finding.severity,
        )
        return AuditFindingRead.model_validate(finding)

    async def get_finding(self, finding_id: str) -> AuditFindingRead | None:
        """Return a single audit finding by ID."""
        import uuid as _uuid

        try:
            uid = _uuid.UUID(finding_id)
        except ValueError:
            return None
        finding = await self._finding_repo.get(uid)
        return AuditFindingRead.model_validate(finding) if finding else None

    async def list_findings(self, limit: int = 50) -> list[AuditFindingRead]:
        """Return a list of audit findings."""
        findings = await self._finding_repo.list(limit=limit)
        return [AuditFindingRead.model_validate(f) for f in findings]

    # ── Three-way matching ────────────────────────────────────────────────────

    def three_way_matching(
        self,
        po_data: DocumentData,
        gr_data: DocumentData,
        invoice_data: DocumentData,
    ) -> MatchResult:
        """Compare quantity and amount between PO, Goods Receipt, and Invoice.

        Tolerance: quantity ±2%, amount ±1%.
        Pure business logic — no I/O needed, no async.
        """
        discrepancies: list[str] = []

        qty_tolerance = Decimal("0.02")
        amt_tolerance = Decimal("0.01")

        # Quantity checks
        if po_data.quantity > 0:
            qty_diff_gr = abs(gr_data.quantity - po_data.quantity) / po_data.quantity
            if qty_diff_gr > qty_tolerance:
                discrepancies.append(
                    f"GR quantity {gr_data.quantity} deviates from PO {po_data.quantity} "
                    f"by {qty_diff_gr * 100:.2f}% (tolerance 2%)"
                )
            qty_diff_inv = abs(invoice_data.quantity - po_data.quantity) / po_data.quantity
            if qty_diff_inv > qty_tolerance:
                discrepancies.append(
                    f"Invoice quantity {invoice_data.quantity} deviates from PO {po_data.quantity} "
                    f"by {qty_diff_inv * 100:.2f}% (tolerance 2%)"
                )

        # Amount checks
        if po_data.amount > 0:
            amt_diff_inv = abs(invoice_data.amount - po_data.amount) / po_data.amount
            if amt_diff_inv > amt_tolerance:
                discrepancies.append(
                    f"Invoice amount {invoice_data.amount} deviates from PO {po_data.amount} "
                    f"by {amt_diff_inv * 100:.2f}% (tolerance 1%)"
                )
            amt_diff_gr = abs(gr_data.amount - po_data.amount) / po_data.amount
            if amt_diff_gr > amt_tolerance:
                discrepancies.append(
                    f"GR amount {gr_data.amount} deviates from PO {po_data.amount} "
                    f"by {amt_diff_gr * 100:.2f}% (tolerance 1%)"
                )

        return MatchResult(matched=len(discrepancies) == 0, discrepancies=discrepancies)

    # ── SOP validation ────────────────────────────────────────────────────────

    def validate_sop(
        self,
        amount: Decimal,
        currency: str,
        has_level2_approval: bool = False,
        has_complete_docs: bool = True,
    ) -> SopValidationResult:
        """Rule-based SOP validation.

        Rules:
        - Transactions > 100 juta IDR require level-2 approval.
        - All documents must be complete.
        """
        violations: list[str] = []

        if currency == "IDR" and amount > _SOP_L2_APPROVAL_THRESHOLD:
            if not has_level2_approval:
                violations.append(
                    f"Transaction amount {amount:,.0f} IDR exceeds 100.000.000 IDR threshold "
                    "— level-2 approval required."
                )

        if not has_complete_docs:
            violations.append("Incomplete documentation — all supporting documents are required.")

        return SopValidationResult(passed=len(violations) == 0, violations=violations)

    # ── Risk report ───────────────────────────────────────────────────────────

    async def generate_risk_report(
        self,
        transaction_id: str,
        po_data: DocumentData | None = None,
        gr_data: DocumentData | None = None,
        invoice_data: DocumentData | None = None,
        has_level2_approval: bool = False,
        has_complete_docs: bool = True,
    ) -> RiskReportResponse:
        """Orchestrate three-way matching + SOP validation, persist findings."""
        findings: list[AuditFindingRead] = []
        overall_status = "PASS"
        severity = "LOW"
        recommendations: list[str] = []

        # 1. Three-way matching (only if all three documents provided)
        if po_data and gr_data and invoice_data:
            match_result = self.three_way_matching(po_data, gr_data, invoice_data)
            if not match_result.matched:
                overall_status = "FAIL"
                severity = "HIGH"
                for disc in match_result.discrepancies:
                    finding_data = AuditFindingCreate(
                        transaction_id=transaction_id,
                        po_number=po_data.reference,
                        severity="HIGH",
                        amount=po_data.amount,
                        description=disc,
                        sop_reference="THREE_WAY_MATCH",
                    )
                    finding = await self._finding_repo.create(finding_data)
                    await self._check_repo.create(
                        CheckResultCreate(finding_id=finding.id, status="FAIL", notes=disc)
                    )
                    findings.append(AuditFindingRead.model_validate(finding))
                    recommendations.append(f"Resolve discrepancy: {disc}")

        # 2. SOP validation
        amount = po_data.amount if po_data else Decimal("0")
        currency = po_data.currency if po_data else "IDR"
        sop_result = self.validate_sop(
            amount=amount,
            currency=currency,
            has_level2_approval=has_level2_approval,
            has_complete_docs=has_complete_docs,
        )
        if not sop_result.passed:
            if overall_status == "PASS":
                overall_status = "WARN"
                severity = "MEDIUM"
            for violation in sop_result.violations:
                finding_data = AuditFindingCreate(
                    transaction_id=transaction_id,
                    po_number=po_data.reference if po_data else "",
                    severity="MEDIUM",
                    amount=amount,
                    description=violation,
                    sop_reference="SOP_VALIDATION",
                )
                finding = await self._finding_repo.create(finding_data)
                await self._check_repo.create(
                    CheckResultCreate(finding_id=finding.id, status="WARN", notes=violation)
                )
                findings.append(AuditFindingRead.model_validate(finding))
                recommendations.append(f"SOP violation: {violation}")

        log.info(
            "risk_report_generated",
            transaction_id=transaction_id,
            status=overall_status,
            finding_count=len(findings),
        )

        return RiskReportResponse(
            transaction_id=transaction_id,
            severity=severity,
            findings=findings,
            overall_status=overall_status,
            recommendation="; ".join(recommendations) if recommendations else "No issues found.",
        )
