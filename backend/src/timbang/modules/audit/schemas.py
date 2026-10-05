"""Pydantic v2 schemas for the audit module."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

# ── AuditFinding ─────────────────────────────────────────────────────────────


class AuditFindingCreate(BaseModel):
    transaction_id: str
    po_number: str = ""
    severity: str = "MEDIUM"
    amount: Decimal = Decimal("0")
    currency: str = "IDR"
    description: str
    sop_reference: str | None = None
    evidence_url: str | None = None
    sop_clause_citation: str | None = None
    evidence_type: str = ""


class AuditFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_id: str
    po_number: str
    severity: str
    amount: Decimal
    currency: str
    description: str
    sop_reference: str | None
    evidence_url: str | None = None
    sop_clause_citation: str | None = None
    evidence_type: str = ""
    created_at: datetime


# ── CheckResult ───────────────────────────────────────────────────────────────


class CheckResultCreate(BaseModel):
    finding_id: uuid.UUID
    status: str = "PASS"
    notes: str | None = None
    evidence_url: str | None = None


class CheckResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID
    status: str
    notes: str | None
    evidence_url: str | None
    checked_at: datetime


# ── Three-way matching ────────────────────────────────────────────────────────


class DocumentData(BaseModel):
    """Generic representation of PO / Goods Receipt / Invoice data."""

    quantity: Decimal
    amount: Decimal
    currency: str = "IDR"
    reference: str = ""


class MatchResult(BaseModel):
    matched: bool
    discrepancies: list[str]


# ── SOP validation ────────────────────────────────────────────────────────────


class SopValidationResult(BaseModel):
    passed: bool
    violations: list[str]


# ── Risk Report ───────────────────────────────────────────────────────────────


class RiskReportResponse(BaseModel):
    """Output of the Checker Agent risk report flow."""

    transaction_id: str
    severity: str
    findings: list[AuditFindingRead]
    overall_status: str  # PASS | WARN | FAIL
    recommendation: str
