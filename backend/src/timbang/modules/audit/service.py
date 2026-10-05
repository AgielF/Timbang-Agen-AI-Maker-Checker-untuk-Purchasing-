"""Audit service — business logic layer (Checker Agent).

Rules (docs/agents/BACKEND_AGENTS.md):
- Does NOT import AsyncSession — only repository interfaces.
- Orchestrates matching, SOP validation, and tax-invoice validation.
"""

from __future__ import annotations

import json
import os
import re
import time
from decimal import Decimal

import httpx
import structlog
from fastapi import UploadFile
from pydantic import ValidationError as PydanticValidationError

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import (
    AuditFindingCreate,
    AuditFindingRead,
    CheckResultCreate,
    DocumentData,
    DocumentExtraction,
    FraudIndication,
    MatchResult,
    RiskReportResponse,
    SopValidationResult,
    TaxInvoiceValidationResult,
)
from timbang.shared.core.config import get_settings
from timbang.shared.core.exceptions import UpstreamError, ValidationError

log = structlog.get_logger(__name__)

# SOP thresholds
_SOP_L2_APPROVAL_THRESHOLD = Decimal("100_000_000")  # 100 juta IDR → level 2 approval required
_MAX_PDF_SIZE_MB = 10
_LANGFLOW_FILE_TWEAK_KEY = "File-xxx"
_MARKDOWN_FENCE_RE = re.compile(r"```(?:json)?\s*(.+?)\s*```", re.DOTALL)


def _extract_langflow_text(data: dict) -> str:
    """Extract output text from Langflow's common response envelope shapes."""
    try:
        text = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
        if isinstance(text, str):
            return text
    except (KeyError, IndexError, TypeError):
        pass

    def search(value: object) -> str | None:
        if isinstance(value, dict):
            text_value = value.get("text")
            if isinstance(text_value, str) and text_value.strip():
                return text_value
            for child in value.values():
                found = search(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = search(child)
                if found:
                    return found
        return None

    return search(data) or json.dumps(data, ensure_ascii=False)


def _parse_document_extraction(text: str, document_type: str) -> DocumentExtraction:
    """Parse JSON or return unstructured model output in the raw_text field."""
    parsed: object = None
    candidates = [text.strip()]
    markdown_match = _MARKDOWN_FENCE_RE.search(text)
    if markdown_match:
        candidates.insert(0, markdown_match.group(1).strip())
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            break
        except (json.JSONDecodeError, ValueError):
            continue

    if isinstance(parsed, dict):
        parsed.setdefault("document_type", document_type)
        try:
            return DocumentExtraction.model_validate(parsed)
        except PydanticValidationError:
            pass

    log.warning(
        "checker_document_parse_failed",
        document_type=document_type,
        raw_preview=text[:300],
    )
    return DocumentExtraction(document_type=document_type, raw_text=text)


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

    async def _extract_document_from_pdf(
        self,
        file: UploadFile,
        document_type: str,
    ) -> DocumentExtraction:
        """Upload one PDF to the Checker Langflow flow and parse its extraction."""
        settings = get_settings()
        flow_id = settings.langflow_checker_flow_id
        if not flow_id:
            raise UpstreamError(
                "LANGFLOW_CHECKER_FLOW_ID belum dikonfigurasi. "
                "Set env var LANGFLOW_CHECKER_FLOW_ID sebelum menggunakan endpoint ini."
            )

        filename = file.filename or ""
        extension = os.path.splitext(filename)[1].lower()
        if extension != ".pdf":
            raise ValidationError("Format file tidak didukung. Unggah dokumen PDF.")

        content = await file.read()
        max_bytes = _MAX_PDF_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(f"File terlalu besar. Maks {_MAX_PDF_SIZE_MB} MB.")
        if b"%PDF-" not in content[:1024]:
            raise ValidationError(f"File '{filename}' bukan PDF yang valid.")

        headers: dict[str, str] = {}
        if settings.langflow_api_key:
            headers["x-api-key"] = settings.langflow_api_key

        try:
            async with httpx.AsyncClient(timeout=settings.langflow_timeout_seconds) as client:
                upload_url = f"{settings.langflow_base_url}/api/v1/files/upload/{flow_id}"
                upload_response = await client.post(
                    upload_url,
                    headers=headers,
                    files={
                        "file": (
                            filename,
                            content,
                            file.content_type or "application/pdf",
                        )
                    },
                )
                if upload_response.status_code not in (200, 201):
                    raise UpstreamError(
                        f"Langflow file upload failed HTTP {upload_response.status_code}: "
                        f"{upload_response.text[:300]}"
                    )
                try:
                    upload_data = upload_response.json()
                    file_path = upload_data["file_path"]
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    raise UpstreamError(
                        "Langflow upload response tidak memiliki file_path."
                    ) from exc

                if not isinstance(file_path, str) or not file_path:
                    raise UpstreamError("Langflow upload response tidak memiliki file_path.")

                run_url = f"{settings.langflow_base_url}/api/v1/run/{flow_id}"
                started_at = time.monotonic()
                run_response = await client.post(
                    run_url,
                    headers={**headers, "Content-Type": "application/json"},
                    json={
                        "input_value": f"Ekstrak dokumen type: {document_type}",
                        "input_type": "chat",
                        "output_type": "chat",
                        "tweaks": {
                            _LANGFLOW_FILE_TWEAK_KEY: {"file_path": file_path},
                        },
                    },
                )
        except httpx.TimeoutException as exc:
            raise UpstreamError(f"Langflow request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(f"Langflow HTTP error: {exc}") from exc

        elapsed_ms = int((time.monotonic() - started_at) * 1000)
        log.info(
            "langflow_checker_document_extracted",
            flow_id=flow_id,
            document_type=document_type,
            status_code=run_response.status_code,
            elapsed_ms=elapsed_ms,
        )
        if run_response.status_code != 200:
            raise UpstreamError(
                f"Langflow returned HTTP {run_response.status_code}: {run_response.text[:300]}"
            )
        try:
            response_data = run_response.json()
        except json.JSONDecodeError as exc:
            raise UpstreamError(f"Langflow response is not valid JSON: {exc}") from exc

        text = _extract_langflow_text(response_data)
        return _parse_document_extraction(text, document_type)

    async def get_risk_report_from_files(
        self,
        tx_id: str,
        po_file: UploadFile,
        gr_file: UploadFile,
        invoice_file: UploadFile,
        tax_invoice_file: UploadFile | None = None,
        has_level2_approval: bool = False,
        has_complete_docs: bool = True,
    ) -> RiskReportResponse:
        """Extract three or four PDF documents, then generate the risk report."""
        po_extraction = await self._extract_document_from_pdf(po_file, "PO")
        gr_extraction = await self._extract_document_from_pdf(gr_file, "GR")
        invoice_extraction = await self._extract_document_from_pdf(invoice_file, "INVOICE")
        tax_invoice_extraction = None
        if tax_invoice_file is not None:
            tax_invoice_extraction = await self._extract_document_from_pdf(
                tax_invoice_file,
                "TAX_INVOICE",
            )

        def to_decimal(value: float | None) -> Decimal | None:
            return Decimal(str(value)) if value is not None else None

        po_data = DocumentData(
            quantity=to_decimal(po_extraction.quantity) or Decimal("0"),
            amount=to_decimal(po_extraction.amount) or Decimal("0"),
            currency=po_extraction.currency,
            reference=po_extraction.reference,
            npwp_vendor=po_extraction.npwp_vendor,
        )
        gr_data = DocumentData(
            quantity=to_decimal(gr_extraction.quantity) or Decimal("0"),
            amount=to_decimal(gr_extraction.amount) or Decimal("0"),
            currency=gr_extraction.currency,
            reference=gr_extraction.reference,
            npwp_vendor=gr_extraction.npwp_vendor,
        )
        invoice_data = DocumentData(
            quantity=to_decimal(invoice_extraction.quantity) or Decimal("0"),
            amount=to_decimal(invoice_extraction.amount) or Decimal("0"),
            currency=invoice_extraction.currency,
            reference=invoice_extraction.reference,
            tax_invoice_ref=invoice_extraction.tax_invoice_ref,
            ppn_amount=to_decimal(invoice_extraction.ppn_amount),
            npwp_vendor=invoice_extraction.npwp_vendor,
            dpp_amount=to_decimal(invoice_extraction.dpp_amount),
        )

        if tax_invoice_extraction is not None:
            invoice_data.tax_invoice_ref = (
                tax_invoice_extraction.tax_invoice_ref or invoice_data.tax_invoice_ref
            )
            invoice_data.dpp_amount = (
                to_decimal(tax_invoice_extraction.dpp_amount)
                if tax_invoice_extraction.dpp_amount is not None
                else invoice_data.dpp_amount
            )
            invoice_data.ppn_amount = (
                to_decimal(tax_invoice_extraction.ppn_amount)
                if tax_invoice_extraction.ppn_amount is not None
                else invoice_data.ppn_amount
            )
            invoice_data.npwp_vendor = (
                tax_invoice_extraction.npwp_vendor or invoice_data.npwp_vendor
            )

        return await self.generate_risk_report(
            transaction_id=tx_id,
            po_data=po_data,
            gr_data=gr_data,
            invoice_data=invoice_data,
            has_level2_approval=has_level2_approval,
            has_complete_docs=has_complete_docs,
        )

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
