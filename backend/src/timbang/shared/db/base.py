"""SQLAlchemy declarative base (2.0 style).

All domain models must inherit from Base.
Import models here (or their packages) so that Alembic autogenerate
can discover them via metadata.

TODO (next session): uncomment imports once models are fleshed out:
    from timbang.modules.procurement import models as _procurement_models  # noqa: F401
    from timbang.modules.audit import models as _audit_models              # noqa: F401
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common declarative base for all SQLAlchemy models."""
