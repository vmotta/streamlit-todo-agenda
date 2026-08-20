from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session, sessionmaker

from organiza.exceptions import NotFoundError, ValidationError
from organiza.models import TaskPriority, TaskStatus
from organiza.schemas import TaskCreate, TaskQuery, TaskUpdate
from organiza.services.tasks import TaskService, task_create_from_values


def test_task_lifecycle_is_persistent_and_idempotent(
    session_factory: sessionmaker[Session], fixed_now: datetime
) -> None:
    service = TaskService(session_factory)
    created = service.create(
        "alice",
        TaskCreate(
            title="  Entregar relatório ",
            priority=TaskPriority.HIGH,
            due_at=fixed_now - timedelta(hours=1),
        ),
    )
    assert created.status == TaskStatus.PENDING
    assert service.is_overdue(created, fixed_now)

    completed = service.complete("alice", created.id, fixed_now)
    again = service.complete("alice", created.id, fixed_now + timedelta(hours=1))
    assert completed.completed_at is not None
    assert again.completed_at == completed.completed_at
    assert not service.is_overdue(again, fixed_now + timedelta(days=1))

    reopened = service.reopen("alice", created.id)
    assert reopened.status == TaskStatus.PENDING
    assert reopened.completed_at is None

    updated = service.update(
        "alice",
        created.id,
        TaskUpdate(title="Relatório final", category="Trabalho", clear_due_at=True),
    )
    assert updated.title == "Relatório final"
    assert updated.category == "Trabalho"
    assert updated.due_at is None

    service.delete("alice", created.id)
    with pytest.raises(NotFoundError):
        service.get("alice", created.id)


def test_task_filters_search_order_and_owner_isolation(
    session_factory: sessionmaker[Session], fixed_now: datetime
) -> None:
    service = TaskService(session_factory)
    low = service.create(
        "alice", TaskCreate(title="Mercado", category="Casa", priority=TaskPriority.LOW)
    )
    high = service.create(
        "alice",
        TaskCreate(
            title="Preparar apresentação",
            description="Reunião trimestral",
            category="Trabalho",
            priority=TaskPriority.HIGH,
            due_at=fixed_now + timedelta(days=1),
        ),
    )
    service.create("bob", TaskCreate(title="Segredo de Bob", priority=TaskPriority.HIGH))

    searched = service.list("alice", TaskQuery(status=None, search="TRIMESTRAL"))
    assert [item.id for item in searched] == [high.id]
    assert service.categories("alice") == ["Casa", "Trabalho"]
    ordered = service.list("alice", TaskQuery(status=None, order_by="priority", descending=True))
    assert [item.id for item in ordered] == [high.id, low.id]
    assert all(item.owner_id == "alice" for item in service.list("alice", TaskQuery(status=None)))

    with pytest.raises(NotFoundError):
        service.get("alice", service.list("bob")[0].id)


def test_task_service_rejects_naive_reference(
    session_factory: sessionmaker[Session], fixed_now: datetime
) -> None:
    service = TaskService(session_factory)
    task = service.create("alice", TaskCreate(title="Teste", due_at=fixed_now))
    with pytest.raises(ValidationError):
        service.complete("alice", task.id, datetime(2026, 8, 20))
    with pytest.raises(ValidationError):
        service.is_overdue(task, datetime(2026, 8, 20))


def test_adapter_converts_pydantic_error_to_domain_error() -> None:
    with pytest.raises(ValidationError):
        task_create_from_values(title="")
