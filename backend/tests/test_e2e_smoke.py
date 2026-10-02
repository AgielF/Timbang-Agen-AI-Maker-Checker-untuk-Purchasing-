"""E2E smoke tests — full request/response cycle via TestClient.

Uses the same in-memory SQLite fixtures from conftest.py.
Each test is independent: uses its own app+session via the conftest
`client` fixture (which is backed by `engine` which creates/drops tables).

For the 9Router recommendation test we monkeypatch httpx.AsyncClient.post
using unittest.mock — no extra dependencies needed.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# ── 1. Health ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "app" in body


# ── 2. Vendor CRUD ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_list_vendors(client):
    # Create
    r = await client.post(
        "/api/v1/procurement/vendors",
        json={"name": "PT Smoke Test", "contact_email": "test@example.com"},
    )
    assert r.status_code == 201
    created = r.json()
    assert "id" in created
    assert created["name"] == "PT Smoke Test"
    assert created["is_active"] is True

    # List — vendor must appear
    r = await client.get("/api/v1/procurement/vendors")
    assert r.status_code == 200
    names = [v["name"] for v in r.json()]
    assert "PT Smoke Test" in names

    # Duplicate name → 400
    r = await client.post(
        "/api/v1/procurement/vendors",
        json={"name": "PT Smoke Test"},
    )
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"]


# ── 3. Submit quotes + cross-validate ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_submit_quote_and_validate_price(client):
    prices = [
        ("Vendor Alpha", Decimal("8500000")),
        ("Vendor Beta", Decimal("8700000")),
        ("Vendor Gamma", Decimal("12500000")),  # outlier
    ]
    vendor_ids = []

    # Create 3 vendors
    for name, _ in prices:
        r = await client.post("/api/v1/procurement/vendors", json={"name": name})
        assert r.status_code == 201
        vendor_ids.append(r.json()["id"])

    # Submit 1 quote per vendor for "Laptop i5"
    outlier_vendor_id = None
    for (_name, price), vid in zip(prices, vendor_ids, strict=True):
        r = await client.post(
            f"/api/v1/procurement/vendors/{vid}/quotes",
            json={
                "vendor_id": vid,
                "item_name": "Laptop i5",
                "price": str(price),
                "currency": "IDR",
            },
        )
        assert r.status_code == 201
        if price == Decimal("12500000"):
            outlier_vendor_id = vid

    # Cross-validate
    r = await client.get("/api/v1/procurement/items/Laptop i5/validate")
    assert r.status_code == 200
    body = r.json()
    assert "median" in body
    assert "flagged_vendor_ids" in body
    assert "spread_percent" in body
    assert Decimal(body["median"]) > 0
    # The outlier vendor must be flagged
    assert outlier_vendor_id in body["flagged_vendor_ids"]
    # Spread must be significant (outlier is ~47% above median)
    assert Decimal(body["spread_percent"]) > Decimal("30")


# ── 4. Recommendation endpoint (mock Langflow) ────────────────────────────────


@pytest.mark.asyncio
async def test_recommendation_endpoint_returns_shape(client, monkeypatch):
    """Mock Langflow HTTP call and verify RecommendationResponse shape."""
    monkeypatch.setattr(
        __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings(),
        "langflow_maker_flow_id",
        "test-flow-id",
    )

    # Seed 3 vendors + quotes
    prices = [
        ("VendorRec1", Decimal("5000000")),
        ("VendorRec2", Decimal("5200000")),
        ("VendorRec3", Decimal("5100000")),
    ]
    vendor_ids = []
    for name, _ in prices:
        r = await client.post("/api/v1/procurement/vendors", json={"name": name})
        assert r.status_code == 201
        vendor_ids.append(r.json()["id"])

    for (_name, price), vid in zip(prices, vendor_ids, strict=True):
        r = await client.post(
            f"/api/v1/procurement/vendors/{vid}/quotes",
            json={"vendor_id": vid, "item_name": "Monitor 27", "price": str(price)},
        )
        assert r.status_code == 201

    # Real Langflow-shaped response with new schema
    langflow_text = (
        '{"vendor_name": "PT Sinar", "items": ['
        '{"nama_item": "Monitor 27", "harga_vendor": 5000000, '
        '"harga_pasar_rata": 5100000, "selisih_persen": -1.96, '
        '"status": "WAJAR", "rekomendasi": "SETUJU", '
        '"sumber": ["https://a"], "alasan": "Harga kompetitif"}]}'
    )
    mock_payload = {"outputs": [{"outputs": [{"results": {"message": {"text": langflow_text}}}]}]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(
            status_code=200,
            json=mock_payload,
            request=httpx.Request("POST", "http://mock"),
        )
        r = await client.get("/api/v1/procurement/items/Monitor 27/recommend")

    assert r.status_code == 200
    body = r.json()
    assert "vendor_name" in body
    assert body["vendor_name"] == "PT Sinar"
    assert "items" in body
    assert len(body["items"]) == 1
    assert body["items"][0]["nama_item"] == "Monitor 27"
    assert body["items"][0]["rekomendasi"] == "SETUJU"


# ── 5. Three-way matching endpoint ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_three_way_matching_endpoint(client):
    # ── All match ───────────────────────────────────────────────────────────
    body_match = {
        "po": {"quantity": "100", "amount": "50000000", "currency": "IDR", "reference": "PO-001"},
        "gr": {"quantity": "100", "amount": "50000000", "currency": "IDR", "reference": "GR-001"},
        "invoice": {
            "quantity": "100",
            "amount": "50200000",  # 0.4% — within 1%
            "currency": "IDR",
            "reference": "INV-001",
        },
    }
    r = await client.post("/api/v1/audit/transactions/TRX-E2E-MATCH/match", json=body_match)
    assert r.status_code == 200
    result = r.json()
    assert result["matched"] is True
    assert result["discrepancies"] == []

    # ── Qty mismatch ────────────────────────────────────────────────────────
    body_mismatch = {
        "po": {"quantity": "100", "amount": "50000000", "currency": "IDR", "reference": "PO-002"},
        "gr": {
            "quantity": "90",  # 10% deviation — exceeds 2% tolerance
            "amount": "50000000",
            "currency": "IDR",
            "reference": "GR-002",
        },
        "invoice": {
            "quantity": "100",
            "amount": "50000000",
            "currency": "IDR",
            "reference": "INV-002",
        },
    }
    r = await client.post("/api/v1/audit/transactions/TRX-E2E-MISMATCH/match", json=body_mismatch)
    assert r.status_code == 200
    result = r.json()
    assert result["matched"] is False
    assert len(result["discrepancies"]) >= 1
    assert any("GR quantity" in d for d in result["discrepancies"])


# ── 6. Risk report endpoint ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_risk_report_creates_finding(client):
    body = {
        "po": {
            "quantity": "50",
            "amount": "150000000",  # > 100jt → SOP violation without L2 approval
            "currency": "IDR",
            "reference": "PO-RISK-001",
        },
        "gr": {"quantity": "50", "amount": "150000000", "currency": "IDR", "reference": "GR-R"},
        "invoice": {
            "quantity": "50",
            "amount": "151500000",  # 1% deviation — at boundary, should FAIL (>1%)
            "currency": "IDR",
            "reference": "INV-R",
        },
        "has_level2_approval": False,
        "has_complete_docs": True,
    }
    r = await client.post("/api/v1/audit/transactions/TRX-NEW-9999/risk-report", json=body)
    assert r.status_code == 200
    result = r.json()
    assert result["transaction_id"] == "TRX-NEW-9999"
    assert "severity" in result
    assert "findings" in result
    assert "overall_status" in result
    assert "recommendation" in result
    # SOP violation must be found (amount > 100jt, no L2 approval)
    assert result["overall_status"] in ("FAIL", "WARN")
    assert len(result["findings"]) >= 1
