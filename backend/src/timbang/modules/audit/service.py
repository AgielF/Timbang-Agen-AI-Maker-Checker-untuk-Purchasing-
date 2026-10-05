"""Audit service — business logic layer (Checker Agent).

Rules (docs/agents/BACKEND_AGENTS.md):
- Does NOT import AsyncSession — only repository interfaces.
- Orchestrates matching, SOP validation, and tax-invoice validation.
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
    FraudIndication,
    MatchResult,
    RiskReportResponse,
    SopValidationResult,
    TaxInvoiceValidationResult,
)

log = structlog.get_logger(__name__)

# SOP thresholds
_SOP_L2_APPROVAL_THRESHOLD = Decimal("100_000_000")  # 100 juta IDR → level 2 approval required


def _is_valid_tax_invoice_ref(ref: str) -> bool:
    if not ref:
        return False
    digits = "".join(character for character in ref if character.isdigit())
    return len(digits) == 16


def _citation_guard(findings: list[dict]) -> list[dict]:
    """Drop findings that have neither a source document nor an SOP citation."""
    valid: list[dict] = []
    for finding in findings:
        has_evidence = bool(finding.get("evidence_url")) or bool(finding.get("sop_clause_citation"))
        if has_evidence:
            valid.append(finding)
        else:
            log.warning(
                f"Citation guard: dropped finding without evidence: "
                f"{finding.get('description', '?')[:80]}"
            )
    return valid


def _indication_for_discrepancy(discrepancy: str) -> FraudIndication:
    text = discrepancy.lower()
    if "quantity" in text:
        return FraudIndication.QTY_DISCREPANCY
    if "amount" in text or "dpp" in text:
        return FraudIndication.PRICE_MANIPULATION
    if "duplicate" in text:
        return FraudIndication.DUPLICATE_INVOICE
    if "split" in text:
        return FraudIndication.SPLIT_PO
    return FraudIndication.UNKNOWN


def _indication_for_sop_violation(violation: str) -> FraudIndication:
    text = violation.lower()
    if "level2" in text or "approval" in text or "l2" in text:
        return FraudIndication.UNAUTHORIZED_APPROVAL
    if "complete" in text or "docs" in text:
        return FraudIndication.INCOMPLETE_DOCS
    return FraudIndication.UNKNOWN


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
        """Compare quantity and value between PO, Goods Receipt, and Invoice.

        Tolerance: quantity ±2%, amount/DPP ±1%.
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
            if invoice_data.dpp_amount is not None and invoice_data.dpp_amount > 0:
                invoice_amount_to_compare = invoice_data.dpp_amount
                invoice_amount_label = "DPP"
            else:
                invoice_amount_to_compare = invoice_data.amount
                invoice_amount_label = "amount"
            amt_diff_inv = abs(invoice_amount_to_compare - po_data.amount) / po_data.amount
            if amt_diff_inv > amt_tolerance:
                discrepancies.append(
                    f"Invoice {invoice_amount_label} {invoice_amount_to_compare} "
                    f"deviates from PO {po_data.amount} "
                    f"by {amt_diff_inv * 100:.2f}% (tolerance 1%)"
                )
            amt_diff_gr = abs(gr_data.amount - po_data.amount) / po_data.amount
            if amt_diff_gr > amt_tolerance:
                discrepancies.append(
                    f"GR amount {gr_data.amount} deviates from PO {po_data.amount} "
                    f"by {amt_diff_gr * 100:.2f}% (tolerance 1%)"
                )

        return MatchResult(matched=len(discrepancies) == 0, discrepancies=discrepancies)

    def validate_tax_invoice(
        self,
        po_data: DocumentData,
        invoice_data: DocumentData,
    ) -> TaxInvoiceValidationResult:
        """Validate the invoice's NPWP, VAT amount, and tax invoice number."""
        violations: list[str] = []
        po_npwp = po_data.npwp_vendor.strip()
        invoice_npwp = invoice_data.npwp_vendor.strip()
        npwp_values = [value for value in (po_npwp, invoice_npwp) if value]

        if not npwp_values:
            violations.append("NPWP vendor kosong — harus 15 digit numerik")
        for npwp in npwp_values:
            digits_only = "".join(character for character in npwp if character.isdigit())
            if len(digits_only) != 15:
                violations.append(f"NPWP '{npwp}' tidak valid — harus 15 digit numerik")

        if po_npwp and invoice_npwp:
            po_digits = "".join(character for character in po_npwp if character.isdigit())
            invoice_digits = "".join(character for character in invoice_npwp if character.isdigit())
            if po_digits != invoice_digits:
                violations.append("NPWP vendor pada PO dan faktur pajak tidak konsisten")

        if invoice_data.ppn_amount is not None and invoice_data.dpp_amount is not None:
            if invoice_data.dpp_amount > 0:
                expected_ppn = invoice_data.dpp_amount * Decimal("0.11")
                actual_ppn = invoice_data.ppn_amount
                diff_pct = abs(actual_ppn - expected_ppn) / expected_ppn * Decimal("100")
                if diff_pct > Decimal("2.0"):
                    violations.append(
                        f"PPN {actual_ppn:,.0f} tidak sesuai — "
                        f"seharusnya ≈{expected_ppn:,.0f} (11% dari DPP)"
                    )

        if invoice_data.ppn_amount is not None and invoice_data.ppn_amount > 0:
            if not invoice_data.tax_invoice_ref.strip():
                violations.append("PPN > 0 tapi nomor faktur pajak kosong")

        tax_invoice_ref = invoice_data.tax_invoice_ref.strip()
        if tax_invoice_ref and not _is_valid_tax_invoice_ref(tax_invoice_ref):
            violations.append(
                f"Nomor faktur pajak '{tax_invoice_ref}' tidak valid — "
                "harus 3 digit kode pajak + 13 digit"
            )

        return TaxInvoiceValidationResult(passed=not violations, violations=violations)

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
        """Orchestrate three-way matching, SOP and tax validation; persist findings."""
        findings: list[AuditFindingRead] = []
        overall_status = "PASS"
        severity = "LOW"
        recommendations: list[str] = []
        pending_findings: list[dict] = []

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
                        evidence_url=f"po:{po_data.reference}" if po_data.reference else None,
                        sop_clause_citation=(
                            "SOP-01: Three-way match tolerance ±2% qty, ±1% amount"
                        ),
                        evidence_type="DISCREPANCY",
                        indication_label=_indication_for_discrepancy(disc),
                    )
                    pending_findings.append(
                        {
                            "description": disc,
                            "evidence_url": finding_data.evidence_url,
                            "sop_clause_citation": finding_data.sop_clause_citation,
                            "finding_data": finding_data,
                            "check_status": "FAIL",
                            "check_notes": disc,
                            "recommendation": f"Resolve discrepancy: {disc}",
                        }
                    )

        # 2. SOP validation
        amount = po_data.amount if po_data else Decimal("0")
        currency = po_data.currency if po_data else "IDR"
        sop_result = self.validate_sop(
            amount=amount,
            currency=currency,
            has_level2_approval=has_level2_approval,
            has_complete_docs=has_complete_docs,
        )
        tax_invoice_result = (
            self.validate_tax_invoice(po_data, invoice_data)
            if po_data is not None and invoice_data is not None
            else None
        )
        if not sop_result.passed:
            if overall_status == "PASS":
                overall_status = "WARN"
                severity = "MEDIUM"
            for violation in sop_result.violations:
                sop_citation = (
                    "SOP: Transactions above IDR 100,000,000 require level-2 approval"
                    if "level-2 approval" in violation
                    else "SOP: All supporting procurement documents must be complete"
                )
                finding_data = AuditFindingCreate(
                    transaction_id=transaction_id,
                    po_number=po_data.reference if po_data else "",
                    severity="MEDIUM",
                    amount=amount,
                    description=violation,
                    sop_reference="SOP_VALIDATION",
                    sop_clause_citation=sop_citation,
                    evidence_type="SOP_THRESHOLD",
                    indication_label=_indication_for_sop_violation(violation),
                )
                pending_findings.append(
                    {
                        "description": violation,
                        "evidence_url": finding_data.evidence_url,
                        "sop_clause_citation": finding_data.sop_clause_citation,
                        "finding_data": finding_data,
                        "check_status": "WARN",
                        "check_notes": violation,
                        "recommendation": f"SOP violation: {violation}",
                    }
                )

        if tax_invoice_result and not tax_invoice_result.passed:
            if overall_status == "PASS":
                overall_status = "WARN"
            tax_has_price_violation = any(
                "ppn" in violation.lower() and "tidak sesuai" in violation.lower()
                for violation in tax_invoice_result.violations
            )
            if tax_has_price_violation:
                severity = "HIGH"
            elif overall_status != "FAIL":
                severity = "MEDIUM"

            for violation in tax_invoice_result.violations:
                is_price_violation = (
                    "ppn" in violation.lower() and "tidak sesuai" in violation.lower()
                )
                finding_data = AuditFindingCreate(
                    transaction_id=transaction_id,
                    po_number=po_data.reference,
                    severity="HIGH" if is_price_violation else "MEDIUM",
                    amount=invoice_data.amount,
                    description=violation,
                    sop_reference="TAX_INVOICE_VALIDATION",
                    evidence_url=f"invoice:{invoice_data.reference}",
                    sop_clause_citation=(
                        "SOP-03: Faktur pajak harus valid — NPWP 15 digit, PPN 11% dari DPP"
                    ),
                    evidence_type="TAX_INVOICE",
                    indication_label=(
                        FraudIndication.PRICE_MANIPULATION
                        if is_price_violation
                        else FraudIndication.INCOMPLETE_DOCS
                    ),
                )
                pending_findings.append(
                    {
                        "description": violation,
                        "evidence_url": finding_data.evidence_url,
                        "sop_clause_citation": finding_data.sop_clause_citation,
                        "finding_data": finding_data,
                        "check_status": "WARN",
                        "check_notes": violation,
                        "recommendation": f"Tax invoice violation: {violation}",
                    }
                )

        # Citation Guard runs before any finding or check result is persisted.
        for candidate in _citation_guard(pending_findings):
            finding = await self._finding_repo.create(candidate["finding_data"])
            await self._check_repo.create(
                CheckResultCreate(
                    finding_id=finding.id,
                    status=candidate["check_status"],
                    notes=candidate["check_notes"],
                )
            )
            findings.append(AuditFindingRead.model_validate(finding))
            recommendations.append(candidate["recommendation"])

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
