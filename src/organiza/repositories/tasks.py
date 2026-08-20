"""Persistência de tarefas com isolamento obrigatório por owner_id."""

from __future__ import annotations

import builtins
from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from organiza.models import Task, TaskPriority, TaskStatus
from organiza.schemas import TaskQuery


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, task: Task) -> Task:
        self.session.add(task)
        self.session.flush()
        self.session.refresh(task)
        return task

    def get(self, owner_id: str, task_id: str) -> Task | None:
        return self.session.scalar(
            select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
        )

    def list(self, owner_id: str, query: TaskQuery) -> builtins.list[Task]:
        statement = select(Task).where(Task.owner_id == owner_id)
        if query.status is not None:
            statement = statement.where(Task.status == query.status)
        if query.priority is not None:
            statement = statement.where(Task.priority == query.priority)
        if query.category:
            statement = statement.where(Task.category == query.category)
        if query.due_from is not None:
            statement = statement.where(Task.due_at >= query.due_from)
        if query.due_to is not None:
            statement = statement.where(Task.due_at < query.due_to)
        if query.search.strip():
            term = f"%{query.search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Task.title).like(term),
                    func.lower(Task.description).like(term),
                    func.lower(Task.category).like(term),
                )
            )

        priority_order = case(
            (Task.priority == TaskPriority.HIGH, 3),
            (Task.priority == TaskPriority.MEDIUM, 2),
            else_=1,
        )
        ordering = {
            "due_at": Task.due_at,
            "priority": priority_order,
            "created_at": Task.created_at,
            "title": func.lower(Task.title),
        }.get(query.order_by, Task.due_at)
        ordering = ordering.desc() if query.descending else ordering.asc()
        return list(
            self.session.scalars(statement.order_by(ordering.nulls_last(), Task.created_at.desc()))
        )

    def due_between(self, owner_id: str, start: datetime, end: datetime) -> builtins.list[Task]:
        return list(
            self.session.scalars(
                select(Task)
                .where(
                    Task.owner_id == owner_id,
                    Task.status == TaskStatus.PENDING,
                    Task.show_on_calendar.is_(True),
                    Task.due_at >= start,
                    Task.due_at < end,
                )
                .order_by(Task.due_at)
            )
        )

    def pending_before(self, owner_id: str, moment: datetime) -> builtins.list[Task]:
        return list(
            self.session.scalars(
                select(Task)
                .where(
                    Task.owner_id == owner_id,
                    Task.status == TaskStatus.PENDING,
                    Task.due_at < moment,
                )
                .order_by(Task.due_at)
            )
        )

    def recently_completed(self, owner_id: str, limit: int = 5) -> builtins.list[Task]:
        return list(
            self.session.scalars(
                select(Task)
                .where(Task.owner_id == owner_id, Task.status == TaskStatus.COMPLETED)
                .order_by(Task.completed_at.desc())
                .limit(limit)
            )
        )

    def categories(self, owner_id: str) -> builtins.list[str]:
        return list(
            self.session.scalars(
                select(Task.category)
                .where(Task.owner_id == owner_id, Task.category != "")
                .distinct()
                .order_by(Task.category)
            )
        )

    def delete(self, task: Task) -> None:
        self.session.delete(task)
