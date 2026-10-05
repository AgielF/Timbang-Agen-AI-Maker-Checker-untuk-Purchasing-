"""Tests for AuditService business logic."""

from __future__ import annotations

from decimal import Decimal

import pytest

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import DocumentData, FraudIndication
from timbang.modules.audit.service import (
    AuditService,
    _citation_guard,
    _indication_for_discrepancy,
)


def _make_service(session) -> AuditService:
    return AuditService(
        finding_repo=AuditFindingRepository(session),
        check_repo=CheckResultRepository(session),
    )


def _doc(qty: str, amount: str, ref: str = "REF-001") -> DocumentData:
    return DocumentData(quantity=Decimal(qty), amount=Decimal(amount), reference=ref)


def _tax_invoice_doc(
    *,
    npwp_vendor: str = "123456789012345",
    ppn_amount: Decimal | None = Decimal("110000"),
    tax_invoice_ref: str = "010.000-26.00000001",
    dpp_amount: Decimal | None = Decimal("1000000"),
) -> DocumentData:
    return DocumentData(
        quantity=Decimal("10"),
        amount=Decimal("1110000"),
        reference="INV-TAX-001",
        npwp_vendor=npwp_vendor,
        ppn_amount=ppn_amount,
        tax_invoice_ref=tax_invoice_ref,
        dpp_amount=dpp_amount,
    )


async def _generate_tax_report(session, invoice_data: DocumentData):
    svc = _make_service(session)
    po = _doc("10", "1000000", ref="PO-TAX-001").model_copy(
        update={"npwp_vendor": "123456789012345"}
    )
    gr = _doc("10", "1000000", ref="GR-TAX-001")
    return await svc.generate_risk_report(
        transaction_id="TXN-TAX-001",
        po_data=po,
        gr_data=gr,
        invoice_data=invoice_data,
        has_level2_approval=True,
        has_complete_docs=True,
    )


def test_citation_guard_drops_finding_without_evidence():
    finding = {
        "description": "Invoice amount exceeds PO amount",
        "evidence_url": None,
        "sop_clause_citation": None,
    }

    assert _citation_guard([finding]) == []


def test_citation_guard_keeps_finding_with_evidence_url():
    finding = {
        "description": "Invoice amount exceeds PO amount",
        "evidence_url": "po:PO-2026-001",
        "sop_clause_citation": None,
    }

    assert _citation_guard([finding]) == [finding]


def test_citation_guard_keeps_finding_with_sop_citation():
    finding = {
        "description": "Transaction exceeds approval threshold",
        "evidence_url": None,
        "sop_clause_citation": "SOP-02: Level-2 approval threshold",
    }

    assert _citation_guard([finding]) == [finding]


# ── three_way_matching ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_three_way_matching_all_match(session):
    """All three documents within tolerance → matched=True, no discrepancies."""
    svc = _make_service(session)
    po = _doc("100", "50000000")
    gr = _doc("100", "50000000")
    inv = _doc("100", "50200000")  # 0.4% deviation — within 1% tolerance
    result = svc.three_way_matching(po, gr, inv)
    assert result.matched is True
    assert result.discrepancies == []


@pytest.mark.asyncio
async def test_three_way_matching_qty_mismatch(session):
    """GR quantity deviates >2% from PO → matched=False with discrepancy message."""
    svc = _make_service(session)
    po = _doc("100", "50000000")
    gr = _doc("95", "50000000")  # 5% qty deviation → exceeds 2% tolerance
    inv = _doc("100", "50000000")
    result = svc.three_way_matching(po, gr, inv)
    assert result.matched is False
    assert any("GR quantity" in d for d in result.discrepancies)


@pytest.mark.asyncio
async def test_three_way_matching_amount_mismatch(session):
    """Invoice amount deviates >1% from PO → matched=False."""
    svc = _make_service(session)
    po = _doc("100", "50000000")
    gr = _doc("100", "50000000")
    inv = _doc("100", "51000000")  # 2% deviation → exceeds 1%
    result = svc.three_way_matching(po, gr, inv)
    assert result.matched is False
    assert any("Invoice amount" in d for d in result.discrepancies)


@pytest.mark.asyncio
async def test_three_way_matching_compares_invoice_dpp_when_available(session):
    svc = _make_service(session)
    po = _doc("100", "100000000")
    gr = _doc("100", "100000000")
    invoice = _doc("100", "111000000").model_copy(update={"dpp_amount": Decimal("100000000")})

    matched = svc.three_way_matching(po, gr, invoice)

    assert matched.matched is True
    assert matched.discrepancies == []

    mismatched_invoice = invoice.model_copy(update={"dpp_amount": Decimal("102000000")})
    mismatch = svc.three_way_matching(po, gr, mismatched_invoice)

    assert mismatch.matched is False
    assert any(
        "Invoice DPP 102000000 deviates from PO 100000000" in discrepancy
        for discrepancy in mismatch.discrepancies
    )
    assert (
        _indication_for_discrepancy(mismatch.discrepancies[0]) == FraudIndication.PRICE_MANIPULATION
    )


# ── validate_sop ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_sop_threshold_violation(session):
    """Amount > 100 juta IDR without level-2 approval → violation."""
    svc = _make_service(session)
    result = svc.validate_sop(
        amount=Decimal("150_000_000"),
        currency="IDR",
        has_level2_approval=False,
    )
    assert result.passed is False
    assert len(result.violations) == 1
    assert "level-2 approval" in result.violations[0]


@pytest.mark.asyncio
async def test_validate_sop_passes_with_approval(session):
    """Amount > 100 juta IDR WITH level-2 approval → no violation."""
    svc = _make_service(session)
    result = svc.validate_sop(
        amount=Decimal("150_000_000"),
        currency="IDR",
        has_level2_approval=True,
    )
    assert result.passed is True
    assert result.violations == []


@pytest.mark.asyncio
async def test_validate_sop_incomplete_docs(session):
    """Incomplete docs → violation regardless of amount."""
    svc = _make_service(session)
    result = svc.validate_sop(
        amount=Decimal("1_000_000"),
        currency="IDR",
        has_complete_docs=False,
    )
    assert result.passed is False
    assert any("documentation" in v for v in result.violations)


# ── generate_risk_report ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_risk_report_persists_findings(session):
    """Risk report with a mismatch must persist AuditFinding + CheckResult."""
    svc = _make_service(session)

    po = _doc("100", "50000000", ref="PO-2024-001")
    gr = _doc("90", "50000000")  # 10% qty deviation
    inv = _doc("100", "51000000")  # 2% amount deviation

    report = await svc.generate_risk_report(
        transaction_id="TXN-001",
        po_data=po,
        gr_data=gr,
        invoice_data=inv,
    )

    assert report.transaction_id == "TXN-001"
    assert report.overall_status == "FAIL"
    assert len(report.findings) >= 1
    assert all(f.evidence_url or f.sop_clause_citation for f in report.findings)
    assert all(f.evidence_type for f in report.findings)
    assert any(f.indication_label == FraudIndication.QTY_DISCREPANCY for f in report.findings)
    assert any(f.indication_label == FraudIndication.PRICE_MANIPULATION for f in report.findings)
    # Findings must be persisted — verify via repository
    findings = await svc._finding_repo.list_by_transaction("TXN-001")
    assert len(findings) >= 1
    assert all(f.evidence_url or f.sop_clause_citation for f in findings)


@pytest.mark.asyncio
async def test_generate_risk_report_labels_missing_level2_approval(session):
    """A high-value transaction without L2 approval gets an approval label."""
    svc = _make_service(session)
    po = _doc("100", "150000000", ref="PO-2026-003").model_copy(
        update={"npwp_vendor": "123456789012345"}
    )
    gr = _doc("100", "150000000", ref="GR-2026-003")
    invoice = _doc("100", "150000000", ref="INV-2026-003").model_copy(
        update={
            "tax_invoice_ref": "0101234567890123",
            "ppn_amount": Decimal("16500000"),
            "npwp_vendor": "123456789012345",
            "dpp_amount": Decimal("150000000"),
        }
    )

    report = await svc.generate_risk_report(
        transaction_id="TXN-003",
        po_data=po,
        gr_data=gr,
        invoice_data=invoice,
        has_level2_approval=False,
        has_complete_docs=True,
    )

    assert len(report.findings) == 1
    assert report.findings[0].indication_label == FraudIndication.UNAUTHORIZED_APPROVAL


@pytest.mark.asyncio
async def test_generate_risk_report_flags_invalid_tax_invoice_npwp(session):
    invoice = _tax_invoice_doc(npwp_vendor="12345")

    report = await _generate_tax_report(session, invoice)

    assert any("NPWP" in finding.description for finding in report.findings)
    assert all(
        finding.indication_label == FraudIndication.INCOMPLETE_DOCS for finding in report.findings
    )


@pytest.mark.asyncio
async def test_generate_risk_report_flags_incorrect_tax_invoice_ppn(session):
    invoice = _tax_invoice_doc(ppn_amount=Decimal("200000"))

    report = await _generate_tax_report(session, invoice)

    assert any(
        "PPN" in finding.description and "tidak sesuai" in finding.description
        for finding in report.findings
    )
    assert any(
        finding.indication_label == FraudIndication.PRICE_MANIPULATION
        for finding in report.findings
    )


@pytest.mark.asyncio
async def test_generate_risk_report_flags_missing_tax_invoice_ref(session):
    invoice = _tax_invoice_doc(tax_invoice_ref="")

    report = await _generate_tax_report(session, invoice)

    assert any("nomor faktur pajak kosong" in finding.description for finding in report.findings)
    assert any(
        finding.indication_label == FraudIndication.INCOMPLETE_DOCS for finding in report.findings
    )


@pytest.mark.asyncio
async def test_generate_risk_report_accepts_valid_tax_invoice(session):
    report = await _generate_tax_report(session, _tax_invoice_doc())

    assert report.findings == []
    assert report.overall_status == "PASS"


@pytest.mark.asyncio
async def test_generate_risk_report_accepts_formatted_efaktur_and_vat_inclusive_total(session):
    svc = _make_service(session)
    po = _doc("100", "100000000", ref="PO-2026-002").model_copy(
        update={"npwp_vendor": "012345678901234"}
    )
    gr = _doc("100", "100000000", ref="GR-2026-002")
    invoice = DocumentData(
        quantity=Decimal("100"),
        amount=Decimal("111000000"),
        currency="IDR",
        reference="INV-2026-002",
        tax_invoice_ref="010.000-26.00000001",
        dpp_amount=Decimal("100000000"),
        ppn_amount=Decimal("11000000"),
        npwp_vendor="012345678901234",
    )

    report = await svc.generate_risk_report(
        transaction_id="TRX-2026-002",
        po_data=po,
        gr_data=gr,
        invoice_data=invoice,
        has_level2_approval=True,
        has_complete_docs=True,
    )

    assert report.overall_status == "PASS"
    assert report.findings == []


@pytest.mark.asyncio
async def test_generate_risk_report_clean_transaction(session):
    """Matching documents + level-2 approval → PASS report with no findings."""
    svc = _make_service(session)

    po = _doc("100", "50000000", ref="PO-2024-002").model_copy(
        update={"npwp_vendor": "123456789012345"}
    )
    gr = _doc("100", "50000000")
    inv = _doc("100", "50200000").model_copy(
        update={
            "tax_invoice_ref": "0101234567890123",
            "ppn_amount": Decimal("5500000"),
            "npwp_vendor": "123456789012345",
            "dpp_amount": Decimal("50000000"),
        }
    )  # 0.4% — within 1%

    report = await svc.generate_risk_report(
        transaction_id="TXN-002",
        po_data=po,
        gr_data=gr,
        invoice_data=inv,
        has_level2_approval=True,
        has_complete_docs=True,
    )

    assert report.overall_status == "PASS"
    assert report.findings == []
    assert "No issues" in report.recommendation
