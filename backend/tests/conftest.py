"""Pytest fixtures shared across all tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from timbang.main import create_app
from timbang.modules.procurement.models import PriceQuote, Vendor
from timbang.shared.core.config import get_settings
from timbang.shared.db.base import Base
from timbang.shared.db.session import get_session

# In-memory SQLite for tests (no real DB required)
_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def disable_external_narrator_flow(monkeypatch):
    """Keep the suite offline unless a test explicitly mocks/enables the narrator."""
    monkeypatch.setattr(get_settings(), "langflow_narrator_flow_id", "")


@pytest_asyncio.fixture
async def engine():
    """Create an in-memory SQLite engine with all tables."""
    _engine = create_async_engine(_TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Provide a raw AsyncSession for direct repository/service tests."""
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        yield s


@pytest_asyncio.fixture
async def app(engine):
    """Create app with get_session overridden to in-memory SQLite."""
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with factory() as s:
            yield s

    application = create_app()
    application.dependency_overrides[get_session] = override_get_session
    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def seed_vendors_and_quotes(session):
    """Seed 3 vendors + 5 quotes for cross_validate_price tests.

    Prices for 'laptop': 10_000_000, 10_200_000, 10_100_000, 10_050_000, 20_000_000 (outlier)
    """
    import uuid

    vendors = []
    for i in range(3):
        v = Vendor(id=uuid.uuid4(), name=f"Vendor {i+1}", is_active=True)
        session.add(v)
        vendors.append(v)
    await session.flush()

    prices = [10_000_000, 10_200_000, 10_100_000, 10_050_000, 20_000_000]
    vendor_ids = [vendors[0].id, vendors[1].id, vendors[2].id, vendors[0].id, vendors[1].id]
    for price, vid in zip(prices, vendor_ids, strict=True):
        q = PriceQuote(id=uuid.uuid4(), vendor_id=vid, item_name="laptop", price=price)
        session.add(q)
    await session.commit()
    return vendors
