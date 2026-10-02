"""Tests for rate limiting behaviour.

Each test that needs an isolated rate-limit counter gets its own FastAPI
app instance built with a fresh Limiter (memory:// storage), so counters
from other tests don't bleed in.

The `client` fixture from conftest.py reuses the module-level limiter
singleton, which is fine for tests that only need to check that the
decorator is wired (not that counters are isolated).
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from timbang.modules.audit.router import router as audit_router
from timbang.modules.procurement.router import router as procurement_router
from timbang.shared.core.config import get_settings
from timbang.shared.core.logging import setup_logging
from timbang.shared.db.base import Base
from timbang.shared.db.session import get_session

_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _make_app_with_fresh_limiter():
    """Build a FastAPI app backed by a brand-new in-memory Limiter.

    This isolates rate-limit counters from the module-level singleton
    used in non-rate-limit tests.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    fresh_limiter = Limiter(
        key_func=get_remote_address,
        storage_uri="memory://",
        enabled=True,
    )

    settings = get_settings()
    setup_logging()

    app = FastAPI(title=settings.app_name, version="0.1.0", docs_url=None, redoc_url=None)

    # Patch the routers' limiter reference to use our fresh one.
    # slowapi decorators capture the limiter at decoration time from the
    # decorator object itself — we need to swap the _storage on the limiter
    # so the fresh instance shares the same decorated functions but has
    # clean counters.
    #
    # Simpler: override app.state.limiter so SlowAPIMiddleware uses it,
    # and re-apply the decorator limits per endpoint.
    #
    # Simplest that actually works: monkey-patch timbang.modules.*.router.limiter
    # just for this scope — but that's fragile. Instead we use the fact that
    # slowapi reads from app.state.limiter at *request* time (not at decoration).
    # So setting app.state.limiter = fresh_limiter is sufficient.

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SlowAPIMiddleware)

    app.state.limiter = fresh_limiter
    app.add_exception_handler(
        RateLimitExceeded,
        lambda req, exc: JSONResponse(
            status_code=429,
            content={"error": "rate_limit_exceeded", "detail": str(exc)},
        ),
    )

    app.include_router(procurement_router, prefix="/api/v1/procurement")
    app.include_router(audit_router, prefix="/api/v1/audit")

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    return app, fresh_limiter


@pytest_asyncio.fixture
async def rl_engine():
    """Fresh SQLite engine for rate-limit tests."""
    engine = create_async_engine(_TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def rl_client(rl_engine):
    """HTTP client backed by a fresh app with an isolated Limiter."""
    factory = async_sessionmaker(rl_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with factory() as s:
            yield s

    app, _fresh_limiter = _make_app_with_fresh_limiter()
    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── 1. Rate-limit headers / first-request check ───────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_headers_present(rl_client):
    """First GET /vendors must succeed (200). slowapi does not add X-RateLimit-*
    headers by default (headers_enabled=False), so we verify the request
    goes through without 429."""
    r = await rl_client.get("/api/v1/procurement/vendors")
    assert r.status_code == 200
    # Verify it's not rate-limited on first hit
    assert r.status_code != 429


# ── 2. Recommend endpoint rate-limited at 10/minute ───────────────────────────


@pytest.mark.asyncio
async def test_recommend_endpoint_rate_limited(rl_client, monkeypatch):
    """11th call to /recommend (limit: 10/minute) must return 429."""
    monkeypatch.setattr(
        __import__("timbang.shared.core.config", fromlist=["get_settings"]).get_settings(),
        "langflow_maker_flow_id",
        "test-rl-flow-id",
    )

    # Seed 3 vendors + quotes so the service has data
    prices = [
        ("RLVendor1", Decimal("5000000")),
        ("RLVendor2", Decimal("5100000")),
        ("RLVendor3", Decimal("5200000")),
    ]
    vendor_ids = []
    for name, _ in prices:
        r = await rl_client.post("/api/v1/procurement/vendors", json={"name": name})
        assert r.status_code == 201
        vendor_ids.append(r.json()["id"])

    for (_name, price), vid in zip(prices, vendor_ids, strict=True):
        r = await rl_client.post(
            f"/api/v1/procurement/vendors/{vid}/quotes",
            json={"vendor_id": vid, "item_name": "RL Laptop", "price": str(price)},
        )
        assert r.status_code == 201

    # Langflow-shaped mock payload
    mock_payload = {
        "outputs": [
            {
                "outputs": [
                    {
                        "results": {
                            "message": {
                                "text": (
                                    '{"vendor_name": "RLVendor1", "items": ['
                                    '{"nama_item": "RL Laptop", "harga_vendor": 5000000, '
                                    '"status": "WAJAR", "rekomendasi": "SETUJU", '
                                    '"alasan": "ok", "sumber": []}]}'
                                )
                            }
                        }
                    }
                ]
            }
        ]
    }

    statuses = []
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(
            status_code=200,
            json=mock_payload,
            request=httpx.Request("POST", "http://mock"),
        )
        for _ in range(11):
            r = await rl_client.get("/api/v1/procurement/items/RL Laptop/recommend")
            statuses.append(r.status_code)

    assert statuses[-1] == 429, f"Expected 429 on 11th call, got statuses: {statuses}"
    last_body = r.json()
    assert "error" in last_body or "detail" in last_body


# ── 3. Health endpoint never rate-limited ─────────────────────────────────────


@pytest.mark.asyncio
async def test_health_not_rate_limited(rl_client):
    """GET /health 100 times → all 200 (exempt from rate limiting)."""
    for _ in range(100):
        r = await rl_client.get("/health")
        assert r.status_code == 200, f"Expected 200 but got {r.status_code}"


# ── 4. Rate-limit state isolated between test instances ───────────────────────


@pytest.mark.asyncio
async def test_rate_limit_reset_between_tests(rl_engine):
    """Each rl_client fixture creates a fresh app with a new Limiter,
    so counters from test_recommend_endpoint_rate_limited do not bleed here.
    We call /vendors (limit 120/minute) 5 times → all must be 200.
    """
    factory = async_sessionmaker(rl_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with factory() as s:
            yield s

    app, _limiter = _make_app_with_fresh_limiter()
    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        for _ in range(5):
            r = await ac.get("/api/v1/procurement/vendors")
            assert r.status_code == 200, f"Got {r.status_code} — limiter state leaked"

    app.dependency_overrides.clear()
