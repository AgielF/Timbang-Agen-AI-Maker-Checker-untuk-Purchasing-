"""Pytest fixtures shared across all tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from timbang.main import create_app
from timbang.shared.db.session import get_session

# In-memory SQLite for tests (no real DB required)
_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def app():
    """Create a fresh app instance with DB session overridden to in-memory SQLite."""
    _engine = create_async_engine(_TEST_DATABASE_URL, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with _session_factory() as session:
            yield session

    application = create_app()
    application.dependency_overrides[get_session] = override_get_session
    yield application

    application.dependency_overrides.clear()
    await _engine.dispose()


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
