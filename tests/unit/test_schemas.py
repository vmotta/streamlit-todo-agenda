from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from organiza.auth import LOCAL_OWNER_ID, resolve_owner_id
from organiza.models import TaskPriority
from organiza.schemas import EventCreate, PreferenceUpdate, TaskCreate, TaskUpdate


def test_task_create_normalizes_and_validates_fields() -> None:
    task = TaskCreate(title="  Comprar   leite  ", category="  Casa  ")
    assert task.title == "Comprar leite"
    assert task.category == "Casa"
    assert task.priority == TaskPriority.MEDIUM

    with pytest.raises(ValidationError):
        TaskCreate(title="   ")
    with pytest.raises(ValidationError):
        TaskCreate(title="x" * 201)
    with pytest.raises(ValidationError):
        TaskUpdate(title="")


def test_task_due_date_must_be_timezone_aware() -> None:
    with pytest.raises(ValidationError, match="fuso"):
        TaskCreate(title="Teste", due_at=datetime(2026, 8, 20, 10, 0))


def test_event_validates_interval_and_timezone() -> None:
    start = datetime(2026, 8, 20, 10, 0, tzinfo=UTC)
    event = EventCreate(title=" Reunião ", start_at=start, end_at=start + timedelta(hours=1))
    assert event.title == "Reunião"

    with pytest.raises(ValidationError, match="anterior"):
        EventCreate(title="Inválido", start_at=start, end_at=start - timedelta(minutes=1))
    with pytest.raises(ValidationError, match="fuso"):
        EventCreate(
            title="Ingênuo",
            start_at=datetime(2026, 8, 20, 10, 0),
            end_at=datetime(2026, 8, 20, 11, 0),
        )


def test_preference_rejects_unknown_timezone() -> None:
    with pytest.raises(ValidationError, match="IANA"):
        PreferenceUpdate(timezone="Mars/Olympus")


def test_owner_resolution_never_uses_editable_input() -> None:
    assert resolve_owner_id("none", {"sub": "ignored"}) == LOCAL_OWNER_ID
    assert resolve_owner_id("oidc", {"sub": "provider-subject"}) == "provider-subject"
    with pytest.raises(Exception, match="identificador seguro"):
        resolve_owner_id("oidc", {"email": "person@example.com"})
    with pytest.raises(Exception, match="Modo"):
        resolve_owner_id("basic")
