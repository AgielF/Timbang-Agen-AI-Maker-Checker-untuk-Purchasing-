"""Tests for AuditService business logic."""

from __future__ import annotations

from decimal import Decimal

import pytest

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import DocumentData
from timbang.modules.audit.service import AuditService


def _make_service(session) -> AuditService:
    return AuditService(
        finding_repo=AuditFindingRepository(session),
        check_repo=CheckResultRepository(session),
    )


def _doc(qty: str, amount: str, ref: str = "REF-001") -> DocumentData:
    return DocumentData(quantity=Decimal(qty), amount=Decimal(amount), reference=ref)


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
    # Findings must be persisted — verify via repository
    findings = await svc._finding_repo.list_by_transaction("TXN-001")
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_generate_risk_report_clean_transaction(session):
    """Matching documents + level-2 approval → PASS report with no findings."""
    svc = _make_service(session)

    po = _doc("100", "50000000", ref="PO-2024-002")
    gr = _doc("100", "50000000")
    inv = _doc("100", "50200000")  # 0.4% — within 1%

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
