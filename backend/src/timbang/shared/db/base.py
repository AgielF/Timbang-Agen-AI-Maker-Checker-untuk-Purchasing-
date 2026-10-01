"""SQLAlchemy declarative base (2.0 style).

All domain models must inherit from Base.
Models are imported here as side-effects so that Alembic autogenerate
discovers all tables via Base.metadata.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common declarative base for all SQLAlchemy models."""


# Side-effect imports — keep at bottom to avoid circular imports
from timbang.modules.audit import models as _audit_models  # noqa: E402, F401
from timbang.modules.procurement import models as _procurement_models  # noqa: E402, F401
