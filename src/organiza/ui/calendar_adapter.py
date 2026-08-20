"""Único adaptador entre o domínio e streamlit-calendar/FullCalendar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from organiza.services.calendar import CalendarItem
from organiza.timeutils import localize


@dataclass(frozen=True)
class CalendarAction:
    kind: Literal["click", "change", "date_click"]
    entity_kind: str | None = None
    entity_id: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None


def to_fullcalendar_events(items: list[CalendarItem], timezone: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        is_task = item.kind == "task_deadline"
        event: dict[str, Any] = {
            "id": f"{item.kind}:{item.id}",
            "title": f"{'[PRAZO]' if is_task else '[EVENTO]'} {item.title}",
            "start": localize(item.start_at, timezone).isoformat(),
            "allDay": item.all_day,
            "backgroundColor": "#B45309" if is_task else "#2563EB",
            "borderColor": "#92400E" if is_task else "#1E40AF",
            "editable": not is_task,
            "extendedProps": {"kind": item.kind, "entity_id": item.id},
        }
        if item.end_at is not None:
            event["end"] = localize(item.end_at, timezone).isoformat()
        result.append(event)
    return result


def parse_calendar_state(state: dict[str, Any] | None) -> CalendarAction | None:
    if not state:
        return None
    callback = state.get("callback")
    payload = state.get(callback, {}) if isinstance(callback, str) else {}
    if not isinstance(payload, dict):
        return None
    if callback == "dateClick":
        raw = payload.get("date") or payload.get("dateStr")
        return CalendarAction(kind="date_click", start_at=_parse_datetime(raw))
    event = payload.get("event", payload)
    if not isinstance(event, dict):
        return None
    extended = event.get("extendedProps", {})
    if not isinstance(extended, dict):
        extended = {}
    raw_id = str(event.get("id", ""))
    raw_kind, _, parsed_id = raw_id.partition(":")
    entity_id = str(extended.get("entity_id") or parsed_id) or None
    entity_kind: str | None = str(extended.get("kind") or raw_kind) or None
    if callback == "eventClick":
        return CalendarAction(kind="click", entity_kind=entity_kind, entity_id=entity_id)
    if callback in {"eventChange", "eventDrop", "eventResize"}:
        return CalendarAction(
            kind="change",
            entity_kind=entity_kind,
            entity_id=entity_id,
            start_at=_parse_datetime(event.get("start")),
            end_at=_parse_datetime(event.get("end")),
        )
    return None


def render_calendar(
    events: list[dict[str, Any]], initial_view: str, timezone: str
) -> dict[str, Any] | None:
    """Renderiza o componente opcional; o chamador sempre mantém a lista fallback."""
    try:
        from streamlit_calendar import calendar
    except ImportError:
        return None
    options = {
        "initialView": initial_view,
        "locale": "pt-br",
        "timeZone": timezone,
        "height": "auto",
        "editable": True,
        "selectable": True,
        "nowIndicator": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay,listMonth",
        },
        "buttonText": {"today": "hoje", "month": "mês", "week": "semana", "day": "dia"},
    }
    result = calendar(
        events=events,
        options=options,
        custom_css=".fc { font-size: 1rem; } .fc-event { cursor: pointer; }",
        callbacks=["dateClick", "eventClick", "eventChange"],
        key=f"organiza-calendar-{initial_view}",
    )
    return result if isinstance(result, dict) else None


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
