from datetime import UTC, datetime, timedelta

from organiza.services.calendar import CalendarItem
from organiza.ui.calendar_adapter import parse_calendar_state, to_fullcalendar_events


def test_fullcalendar_adapter_distinguishes_items_with_text() -> None:
    start = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    events = to_fullcalendar_events(
        [
            CalendarItem("1", "event", "Reunião", start, start + timedelta(hours=1), False),
            CalendarItem("2", "task_deadline", "Entrega", start, None, False),
        ],
        "America/Sao_Paulo",
    )
    assert events[0]["title"].startswith("[EVENTO]")
    assert events[1]["title"].startswith("[PRAZO]")
    assert events[0]["editable"] is True
    assert events[1]["editable"] is False


def test_calendar_callbacks_are_parsed_safely() -> None:
    clicked = parse_calendar_state(
        {
            "callback": "eventClick",
            "eventClick": {"event": {"id": "event:abc", "extendedProps": {}}},
        }
    )
    assert clicked is not None and clicked.entity_id == "abc" and clicked.kind == "click"

    changed = parse_calendar_state(
        {
            "callback": "eventChange",
            "eventChange": {
                "event": {
                    "id": "event:abc",
                    "start": "2026-08-20T10:00:00Z",
                    "end": "2026-08-20T11:00:00Z",
                }
            },
        }
    )
    assert changed is not None and changed.start_at is not None and changed.end_at is not None
    assert parse_calendar_state({"callback": "unknown"}) is None
    assert parse_calendar_state(None) is None
