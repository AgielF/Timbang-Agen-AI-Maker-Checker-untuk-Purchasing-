"""Audit repository — the ONLY layer that uses AsyncSession in this module."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from timbang.modules.audit.models import AuditFinding, CheckResult
from timbang.modules.audit.schemas import AuditFindingCreate, CheckResultCreate


class AuditFindingRepository:
    """Data access layer for AuditFinding entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> AuditFinding | None:
        result = await self._session.execute(
            select(AuditFinding).where(AuditFinding.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: AuditFindingCreate) -> AuditFinding:
        finding = AuditFinding(**data.model_dump())
        self._session.add(finding)
        await self._session.commit()
        await self._session.refresh(finding)
        return finding

    async def list(self, limit: int = 50) -> list[AuditFinding]:
        result = await self._session.execute(select(AuditFinding).limit(limit))
        return list(result.scalars().all())


class CheckResultRepository:
    """Data access layer for CheckResult entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> CheckResult | None:
        result = await self._session.execute(
            select(CheckResult).where(CheckResult.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: CheckResultCreate) -> CheckResult:
        check = CheckResult(**data.model_dump())
        self._session.add(check)
        await self._session.commit()
        await self._session.refresh(check)
        return check

    async def list(self, limit: int = 50) -> list[CheckResult]:
        result = await self._session.execute(select(CheckResult).limit(limit))
        return list(result.scalars().all())
