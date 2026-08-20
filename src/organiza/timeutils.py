"""Operações de data/hora consistentes entre SQLite e PostgreSQL."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def as_utc(value: datetime) -> datetime:
    """Restaura UTC em valores SQLite e normaliza valores aware."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def local_day_bounds(day: date, timezone: str) -> tuple[datetime, datetime]:
    zone = ZoneInfo(timezone)
    start = datetime.combine(day, time.min, zone).astimezone(UTC)
    return start, (datetime.combine(day, time.min, zone) + timedelta(days=1)).astimezone(UTC)


def localize(value: datetime, timezone: str) -> datetime:
    return as_utc(value).astimezone(ZoneInfo(timezone))
