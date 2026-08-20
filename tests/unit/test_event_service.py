from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session, sessionmaker

from organiza.exceptions import NotFoundError, ValidationError
from organiza.schemas import EventCreate, EventUpdate
from organiza.services.events import EventService


def test_event_crud_and_reschedule(session_factory: sessionmaker[Session]) -> None:
    service = EventService(session_factory)
    start = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    created = service.create(
        "alice",
        EventCreate(
            title="Consulta",
            start_at=start,
            end_at=start + timedelta(hours=1),
            location="Centro",
        ),
    )
    assert created.location == "Centro"

    updated = service.update(
        "alice", created.id, EventUpdate(title="Consulta médica", category="Saúde")
    )
    assert updated.title == "Consulta médica"
    moved = service.reschedule(
        "alice", created.id, start + timedelta(days=1), start + timedelta(days=1, hours=2)
    )
    assert moved.end_at > moved.start_at
    assert len(service.list_between("alice", start, start + timedelta(days=3))) == 1
    assert service.upcoming("alice", start)[0].id == created.id

    service.delete("alice", created.id)
    with pytest.raises(NotFoundError):
        service.get("alice", created.id)


def test_event_rejects_invalid_update_and_owner(session_factory: sessionmaker[Session]) -> None:
    service = EventService(session_factory)
    start = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    created = service.create(
        "bob", EventCreate(title="Privado", start_at=start, end_at=start + timedelta(hours=1))
    )
    with pytest.raises(NotFoundError):
        service.update("alice", created.id, EventUpdate(title="Tentativa"))
    with pytest.raises(PydanticValidationError):
        service.update(
            "bob",
            created.id,
            EventUpdate(start_at=start + timedelta(hours=2), end_at=start),
        )


def test_event_period_requires_aware_ordered_dates(
    session_factory: sessionmaker[Session], fixed_now: datetime
) -> None:
    service = EventService(session_factory)
    with pytest.raises(ValidationError, match="fuso"):
        service.list_between("alice", datetime(2026, 1, 1), datetime(2026, 1, 2))
    with pytest.raises(ValidationError, match="anterior"):
        service.list_between("alice", fixed_now, fixed_now - timedelta(days=1))
    with pytest.raises(ValidationError, match="fuso"):
        service.upcoming("alice", datetime(2026, 1, 1))


def test_all_day_event_uses_valid_exclusive_interval(
    session_factory: sessionmaker[Session], fixed_now: datetime
) -> None:
    service = EventService(session_factory)
    result = service.create(
        "alice",
        EventCreate(
            title="Feriado",
            start_at=fixed_now,
            end_at=fixed_now + timedelta(days=1),
            all_day=True,
        ),
    )
    assert result.all_day is True
    assert result.end_at - result.start_at == timedelta(days=1)
