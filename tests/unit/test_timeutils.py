from datetime import UTC, date, datetime

from organiza.timeutils import as_utc, local_day_bounds, localize


def test_sqlite_naive_datetime_is_restored_as_utc() -> None:
    value = as_utc(datetime(2026, 8, 20, 12, 0))
    assert value.tzinfo is UTC
    assert localize(value, "America/Sao_Paulo").hour == 9


def test_local_day_bounds_respect_dst_zone() -> None:
    start, end = local_day_bounds(date(2026, 3, 8), "America/New_York")
    assert start.tzinfo is UTC
    assert (end - start).total_seconds() == 23 * 3600
