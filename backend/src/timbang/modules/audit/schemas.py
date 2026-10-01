"""Pydantic v2 schemas for the audit module."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── AuditFinding ─────────────────────────────────────────────────────────────

class AuditFindingCreate(BaseModel):
    transaction_id: str
    severity: str = "medium"
    description: str


class AuditFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_id: str
    severity: str
    description: str
    created_at: datetime


# ── CheckResult ───────────────────────────────────────────────────────────────

class CheckResultCreate(BaseModel):
    finding_id: uuid.UUID
    status: str = "pending"


class CheckResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID
    status: str
    checked_at: datetime


# ── Risk Report ───────────────────────────────────────────────────────────────

class RiskReportResponse(BaseModel):
    """Output of the Checker Agent risk report flow."""

    # TODO (next session): populate from three-way matching & SOP validation
    total_findings: int = 0
    high_risk_count: int = 0
    compliance_status: str = "unknown"
    summary: str = ""
