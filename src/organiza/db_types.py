"""Tipos SQLAlchemy portáveis entre SQLite e PostgreSQL."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Persiste em UTC e sempre devolve um datetime timezone-aware."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        normalized = value.astimezone(UTC)
        return normalized.replace(tzinfo=None) if dialect.name == "sqlite" else normalized

    def process_result_value(self, value: datetime | None, _dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @property
    def python_type(self) -> type[Any]:
        return datetime
