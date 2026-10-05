"""Tests for AuditService business logic."""

from __future__ import annotations

import io
import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import UploadFile

from timbang.modules.audit.repository import AuditFindingRepository, CheckResultRepository
from timbang.modules.audit.schemas import (
    DocumentData,
    DocumentExtraction,
    FraudIndication,
    MultiDocumentExtraction,
    RiskReportResponse,
)
from timbang.modules.audit.service import (
    AuditService,
    _citation_guard,
    _indication_for_discrepancy,
    _parse_multi_document_extraction,
)
from timbang.shared.core.exceptions import ValidationError


def _make_service(session) -> AuditService:
    return AuditService(
        finding_repo=AuditFindingRepository(session),
        check_repo=CheckResultRepository(session),
    )


def _doc(qty: str, amount: str, ref: str = "REF-001") -> DocumentData:
    return DocumentData(quantity=Decimal(qty), amount=Decimal(amount), reference=ref)


def _pdf_upload(filename: str, content: bytes = b"%PDF-1.7 mock PDF") -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        size=len(content),
        headers={"content-type": "application/pdf"},
    )


def _multi_document_text(*, include_tax: bool = True) -> str:
    documents = {
        "po": {
            "document_type": "PO",
            "reference": "PO-PDF-001",
            "quantity": 10,
            "amount": 100000,
            "currency": "IDR",
            "npwp_vendor": "123456789012345",
        },
        "gr": {
            "document_type": "GR",
            "reference": "GR-PDF-001",
            "quantity": 10,
            "amount": 100000,
            "currency": "IDR",
        },
        "invoice": {
            "document_type": "INVOICE",
            "reference": "INV-PDF-001",
            "quantity": 10,
            "amount": 111000 if include_tax else 100000,
            "currency": "IDR",
        },
    }
    if include_tax:
        documents["tax_invoice"] = {
            "document_type": "TAX_INVOICE",
            "reference": "010.000-26.00000001",
            "dpp_amount": 100000,
            "ppn_amount": 11000,
            "npwp_vendor": "123456789012345",
        }
    return json.dumps(documents)


def _mock_langflow_post(
    call_log: list[dict],
    *,
    include_tax: bool = True,
    malformed_output: bool = False,
):
    async def mock_post(url, **kwargs):
        call_log.append({"url": url, **kwargs})
        if "/files/upload/" in url:
            filename = kwargs["files"]["file"][0]
            return httpx.Response(
                201,
                json={"file_path": f"checker-flow/{filename}"},
                request=httpx.Request("POST", url),
            )

        text = "not valid structured extraction" if malformed_output else _multi_document_text(
            include_tax=include_tax
        )
        payload = {
            "outputs": [
                {
                    "outputs": [
                        {
                            "results": {
                                "message": {
                                    "text": text
                                }
                            }
                        }
                    ]
                }
            ]
        }
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("POST", url),
        )

    return mock_post


def test_parse_multi_document_extraction_with_null_fields():
    text = json.dumps(
        {
            "po": {
                "reference": "PO-001",
                "quantity": 100,
                "amount": 100000000,
                "currency": None,
                "tax_invoice_ref": None,
                "npwp_vendor": None,
            },
            "gr": {
                "reference": "GR-001",
                "quantity": 95,
                "amount": None,
                "currency": None,
                "document_type": None,
            },
            "invoice": {
                "reference": None,
                "quantity": 100,
                "amount": 111000000,
                "currency": "IDR",
            },
        }
    )

    extraction = _parse_multi_document_extraction(text)

    assert extraction.raw_text is None
    assert extraction.po is not None
    assert extraction.po.reference == "PO-001"
    assert extraction.po.currency == ""
    assert extraction.po.tax_invoice_ref == ""
    assert extraction.po.npwp_vendor == ""
    assert extraction.gr is not None
    assert extraction.gr.amount is None
    assert extraction.gr.currency == ""
    assert extraction.gr.document_type == ""
    assert extraction.invoice is not None
    assert extraction.invoice.reference == ""
    assert extraction.invoice.currency == "IDR"


@pytest.mark.asyncio
async def test_gr_amount_fallback_from_po_when_null(session):
    """If GR amount is missing, derive its value proportionally from PO quantity."""
    svc = _make_service(session)
    svc._extract_all_documents = AsyncMock(
        return_value=MultiDocumentExtraction(
            po=DocumentExtraction(
                quantity=100,
                amount=100_000_000,
                currency="IDR",
            ),
            gr=DocumentExtraction(quantity=95, amount=None, currency="IDR"),
            invoice=DocumentExtraction(
                quantity=100,
                amount=111_000_000,
                currency="IDR",
                dpp_amount=100_000_000,
                ppn_amount=11_000_000,
            ),
        )
    )
    svc.generate_risk_report = AsyncMock(
        return_value=RiskReportResponse(
            transaction_id="TXN-GR-FALLBACK",
            severity="LOW",
            findings=[],
            overall_status="PASS",
            recommendation="No issues found.",
        )
    )

    await svc.get_risk_report_from_files(
        tx_id="TXN-GR-FALLBACK",
        po_file=_pdf_upload("po.pdf"),
        gr_file=_pdf_upload("gr.pdf"),
        invoice_file=_pdf_upload("invoice.pdf"),
    )

    kwargs = svc.generate_risk_report.await_args.kwargs
    assert kwargs["gr_data"].amount == Decimal("95000000")


@pytest.mark.asyncio
async def test_gr_currency_fallback_from_po(session):
    """Missing GR and invoice currencies inherit the PO currency."""
    svc = _make_service(session)
    svc._extract_all_documents = AsyncMock(
        return_value=MultiDocumentExtraction(
            po=DocumentExtraction(
                quantity=100,
                amount=100_000_000,
                currency="IDR",
            ),
            gr=DocumentExtraction(quantity=95, amount=95_000_000, currency=""),
            invoice=DocumentExtraction(
                quantity=100,
                amount=100_000_000,
                currency="",
            ),
        )
    )
    svc.generate_risk_report = AsyncMock(
        return_value=RiskReportResponse(
            transaction_id="TXN-CURRENCY-FALLBACK",
            severity="LOW",
            findings=[],
            overall_status="PASS",
            recommendation="No issues found.",
        )
    )

    await svc.get_risk_report_from_files(
        tx_id="TXN-CURRENCY-FALLBACK",
        po_file=_pdf_upload("po.pdf"),
        gr_file=_pdf_upload("gr.pdf"),
        invoice_file=_pdf_upload("invoice.pdf"),
    )

    kwargs = svc.generate_risk_report.await_args.kwargs
    assert kwargs["gr_data"].currency == "IDR"
    assert kwargs["invoice_data"].currency == "IDR"


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
async def test_generate_risk_report_with_narrative(session, monkeypatch):
    settings = __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings()
    monkeypatch.setattr(settings, "langflow_narrator_flow_id", "risk-narrator-test")
    svc = _make_service(session)
    narrative_payload = {
        "executive_summary": "GR received 5% fewer units than the purchase order.",
        "pattern_analysis": ["Quantity shortfall requires vendor follow-up."],
        "dynamic_recommendations": ["Reconcile the 5 missing units with the vendor."],
    }
    langflow_response = {
        "outputs": [
            {
                "outputs": [
                    {"results": {"message": {"text": json.dumps(narrative_payload)}}}
                ]
            }
        ]
    }
    request_log: list[dict] = []

    async def mock_post(url, **kwargs):
        request_log.append({"url": url, **kwargs})
        return httpx.Response(
            200,
            json=langflow_response,
            request=httpx.Request("POST", url),
        )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=mock_post):
        report = await svc.generate_risk_report(
            transaction_id="TXN-NARRATIVE-001",
            po_data=_doc("100", "1000000", ref="PO-NARRATIVE-001").model_copy(
                update={"npwp_vendor": "123456789012345"}
            ),
            gr_data=_doc("95", "950000"),
            invoice_data=_doc("100", "1000000").model_copy(
                update={"npwp_vendor": "123456789012345"}
            ),
            has_level2_approval=True,
        )

    assert len(request_log) == 1
    assert request_log[0]["url"].endswith("/api/v1/run/risk-narrator-test")
    assert "Transaction: TXN-NARRATIVE-001" in request_log[0]["json"]["input_value"]
    assert f"Total Findings: {len(report.findings)}" in request_log[0]["json"]["input_value"]
    assert report.narrative is not None
    assert report.narrative.executive_summary == narrative_payload["executive_summary"]
    assert report.narrative.pattern_analysis == narrative_payload["pattern_analysis"]
    assert report.narrative.dynamic_recommendations == narrative_payload[
        "dynamic_recommendations"
    ]


@pytest.mark.asyncio
async def test_generate_risk_report_without_narrator_flow_id(session, monkeypatch):
    settings = __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings()
    monkeypatch.setattr(settings, "langflow_narrator_flow_id", "")
    svc = _make_service(session)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        report = await svc.generate_risk_report(
            transaction_id="TXN-NO-NARRATOR",
            po_data=_doc("100", "1000000", ref="PO-NO-NARRATOR").model_copy(
                update={"npwp_vendor": "123456789012345"}
            ),
            gr_data=_doc("100", "1000000"),
            invoice_data=_doc("100", "1000000").model_copy(
                update={"npwp_vendor": "123456789012345"}
            ),
            has_level2_approval=True,
        )

    mock_post.assert_not_awaited()
    assert report.narrative is None


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


@pytest.mark.asyncio
async def test_get_risk_report_from_files_happy_path(session, monkeypatch):
    monkeypatch.setattr(
        __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings(),
        "langflow_checker_flow_id",
        "checker-flow-id",
    )
    svc = _make_service(session)
    call_log: list[dict] = []
    original_generate_risk_report = svc.generate_risk_report
    mapped_invoice_data: dict[str, DocumentData] = {}

    async def capture_generate_risk_report(**kwargs):
        mapped_invoice_data["invoice"] = kwargs["invoice_data"]
        return await original_generate_risk_report(**kwargs)

    svc.generate_risk_report = capture_generate_risk_report

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=_mock_langflow_post(call_log),
    ):
        report = await svc.get_risk_report_from_files(
            tx_id="TXN-PDF-HAPPY",
            po_file=_pdf_upload("po.pdf"),
            gr_file=_pdf_upload("gr.pdf"),
            invoice_file=_pdf_upload("invoice.pdf"),
            tax_invoice_file=_pdf_upload("tax-invoice.pdf"),
            has_level2_approval=True,
        )

    assert report.transaction_id == "TXN-PDF-HAPPY"
    assert report.overall_status == "PASS"
    assert report.findings == []
    assert mapped_invoice_data["invoice"].tax_invoice_ref == "010.000-26.00000001"
    findings = await svc._finding_repo.list_by_transaction("TXN-PDF-HAPPY")
    assert findings == []
    assert len(call_log) == 5  # 4 uploads + 1 extraction call
    run_calls = [call for call in call_log if "/api/v1/run/" in call["url"]]
    assert len(run_calls) == 1
    assert run_calls[0]["json"]["input_value"] == "Ekstrak semua dokumen pengadaan"
    assert run_calls[0]["json"]["tweaks"] == {
        "File-po": {"file_path": "checker-flow/po.pdf"},
        "File-gr": {"file_path": "checker-flow/gr.pdf"},
        "File-invoice": {"file_path": "checker-flow/invoice.pdf"},
        "File-tax-invoice": {"file_path": "checker-flow/tax-invoice.pdf"},
    }


@pytest.mark.asyncio
async def test_get_risk_report_from_files_without_tax_invoice(session, monkeypatch):
    monkeypatch.setattr(
        __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings(),
        "langflow_checker_flow_id",
        "checker-flow-id",
    )
    svc = _make_service(session)
    call_log: list[dict] = []

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=_mock_langflow_post(call_log, include_tax=False),
    ):
        report = await svc.get_risk_report_from_files(
            tx_id="TXN-PDF-NO-TAX",
            po_file=_pdf_upload("po.pdf"),
            gr_file=_pdf_upload("gr.pdf"),
            invoice_file=_pdf_upload("invoice.pdf"),
            has_level2_approval=True,
        )

    assert report.transaction_id == "TXN-PDF-NO-TAX"
    assert report.overall_status == "PASS"
    assert report.findings == []
    assert len(call_log) == 4  # 3 uploads + 1 extraction call
    run_calls = [call for call in call_log if "/api/v1/run/" in call["url"]]
    assert len(run_calls) == 1
    assert set(run_calls[0]["json"]["tweaks"]) == {
        "File-po",
        "File-gr",
        "File-invoice",
    }


@pytest.mark.asyncio
async def test_get_risk_report_from_files_handles_invalid_pdf(session, monkeypatch):
    monkeypatch.setattr(
        __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings(),
        "langflow_checker_flow_id",
        "checker-flow-id",
    )
    svc = _make_service(session)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        with pytest.raises(ValidationError, match="bukan PDF yang valid"):
            await svc.get_risk_report_from_files(
                tx_id="TXN-PDF-INVALID",
                po_file=_pdf_upload("po.pdf", b"this is not a PDF"),
                gr_file=_pdf_upload("gr.pdf"),
                invoice_file=_pdf_upload("invoice.pdf"),
            )

    mock_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_risk_report_from_files_rejects_invalid_extension(session, monkeypatch):
    monkeypatch.setattr(
        __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings(),
        "langflow_checker_flow_id",
        "checker-flow-id",
    )
    svc = _make_service(session)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        with pytest.raises(ValidationError, match="Format file tidak didukung"):
            await svc.get_risk_report_from_files(
                tx_id="TXN-PDF-EXTENSION",
                po_file=_pdf_upload("po.txt", b"%PDF-1.7 valid signature"),
                gr_file=_pdf_upload("gr.pdf"),
                invoice_file=_pdf_upload("invoice.pdf"),
            )

    mock_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_extract_all_documents_malformed_output_falls_back_to_raw_text(
    session,
    monkeypatch,
):
    monkeypatch.setattr(
        __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings(),
        "langflow_checker_flow_id",
        "checker-flow-id",
    )
    svc = _make_service(session)
    call_log: list[dict] = []

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=_mock_langflow_post(call_log, malformed_output=True),
    ):
        extraction = await svc._extract_all_documents(
            po_file=_pdf_upload("po.pdf"),
            gr_file=_pdf_upload("gr.pdf"),
            invoice_file=_pdf_upload("invoice.pdf"),
            tax_invoice_file=_pdf_upload("tax-invoice.pdf"),
        )

    assert extraction.po is None
    assert extraction.gr is None
    assert extraction.invoice is None
    assert extraction.tax_invoice is None
    assert extraction.raw_text == "not valid structured extraction"
    assert len([call for call in call_log if "/api/v1/run/" in call["url"]]) == 1
