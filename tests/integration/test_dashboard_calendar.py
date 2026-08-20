from datetime import datetime, timedelta

from sqlalchemy.orm import Session, sessionmaker

from organiza.schemas import EventCreate, PreferenceUpdate, TaskCreate
from organiza.services.calendar import CalendarService
from organiza.services.dashboard import DashboardService
from organiza.services.events import EventService
from organiza.services.preferences import PreferenceService
from organiza.services.tasks import TaskService


def test_dashboard_reflects_database(
    session_factory: sessionmaker[Session], fixed_now: datetime
) -> None:
    tasks = TaskService(session_factory)
    events = EventService(session_factory)
    tasks.create("alice", TaskCreate(title="Atrasada", due_at=fixed_now - timedelta(days=1)))
    tasks.create("alice", TaskCreate(title="Hoje", due_at=fixed_now + timedelta(hours=1)))
    done = tasks.create("alice", TaskCreate(title="Feita"))
    tasks.complete("alice", done.id, fixed_now)
    events.create(
        "alice",
        EventCreate(
            title="Reunião",
            start_at=fixed_now + timedelta(hours=2),
            end_at=fixed_now + timedelta(hours=3),
        ),
    )

    snapshot = DashboardService(session_factory).snapshot("alice", fixed_now, "America/Sao_Paulo")
    assert snapshot.pending_count == 2
    assert [item.title for item in snapshot.overdue] == ["Atrasada"]
    assert [item.title for item in snapshot.tasks_today] == ["Hoje"]
    assert [item.title for item in snapshot.events_today] == ["Reunião"]
    assert [item.title for item in snapshot.recently_completed] == ["Feita"]


def test_calendar_composes_deadlines_without_event_duplication(
    session_factory: sessionmaker[Session], fixed_now: datetime
) -> None:
    task = TaskService(session_factory).create(
        "alice", TaskCreate(title="Prazo", due_at=fixed_now, show_on_calendar=True)
    )
    event = EventService(session_factory).create(
        "alice",
        EventCreate(title="Evento", start_at=fixed_now, end_at=fixed_now + timedelta(hours=1)),
    )
    service = CalendarService(session_factory)
    items = service.list_items(
        "alice", fixed_now - timedelta(days=1), fixed_now + timedelta(days=1)
    )
    assert {(item.kind, item.id) for item in items} == {
        ("task_deadline", task.id),
        ("event", event.id),
    }
    assert len(EventService(session_factory).upcoming("alice", fixed_now)) == 1
    assert [
        item.kind
        for item in service.list_items(
            "alice",
            fixed_now - timedelta(days=1),
            fixed_now + timedelta(days=1),
            include_task_deadlines=False,
        )
    ] == ["event"]


def test_preferences_are_persistent_per_owner(session_factory: sessionmaker[Session]) -> None:
    service = PreferenceService(session_factory, "America/Sao_Paulo")
    initial = service.get("alice")
    assert initial.timezone == "America/Sao_Paulo"
    service.update(
        "alice",
        PreferenceUpdate(timezone="Europe/Lisbon", show_completed=False, show_task_deadlines=False),
    )
    assert service.get("alice").timezone == "Europe/Lisbon"
    assert service.get("bob").show_completed is True
