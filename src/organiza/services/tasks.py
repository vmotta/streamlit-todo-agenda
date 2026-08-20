"""Casos de uso de tarefas."""

from __future__ import annotations

import builtins
import logging
from datetime import UTC, datetime

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from organiza.db import session_scope
from organiza.exceptions import NotFoundError, PersistenceError, ValidationError
from organiza.models import Task, TaskStatus
from organiza.repositories.tasks import TaskRepository
from organiza.schemas import TaskCreate, TaskQuery, TaskRead, TaskUpdate
from organiza.timeutils import as_utc

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create(self, owner_id: str, data: TaskCreate) -> TaskRead:
        task = Task(owner_id=owner_id, **data.model_dump())
        try:
            with session_scope(self.session_factory) as session:
                created = TaskRepository(session).add(task)
                result = TaskRead.model_validate(created)
            logger.info("task_created owner=%s task=%s", owner_id, result.id)
            return result
        except SQLAlchemyError as exc:
            logger.error("task_create_failed owner=%s", owner_id, exc_info=True)
            raise PersistenceError("Não foi possível salvar a tarefa.") from exc

    def get(self, owner_id: str, task_id: str) -> TaskRead:
        with session_scope(self.session_factory) as session:
            task = self._required(TaskRepository(session), owner_id, task_id)
            return TaskRead.model_validate(task)

    def list(self, owner_id: str, query: TaskQuery | None = None) -> builtins.list[TaskRead]:
        with session_scope(self.session_factory) as session:
            tasks = TaskRepository(session).list(owner_id, query or TaskQuery())
            return [TaskRead.model_validate(item) for item in tasks]

    def categories(self, owner_id: str) -> builtins.list[str]:
        with session_scope(self.session_factory) as session:
            return TaskRepository(session).categories(owner_id)

    def update(self, owner_id: str, task_id: str, data: TaskUpdate) -> TaskRead:
        try:
            with session_scope(self.session_factory) as session:
                task = self._required(TaskRepository(session), owner_id, task_id)
                changes = data.model_dump(exclude_unset=True, exclude={"clear_due_at"})
                if data.clear_due_at:
                    changes["due_at"] = None
                for field, value in changes.items():
                    setattr(task, field, value)
                task.updated_at = datetime.now(UTC)
                session.flush()
                result = TaskRead.model_validate(task)
            logger.info("task_updated owner=%s task=%s", owner_id, task_id)
            return result
        except SQLAlchemyError as exc:
            logger.error("task_update_failed owner=%s task=%s", owner_id, task_id, exc_info=True)
            raise PersistenceError("Não foi possível atualizar a tarefa.") from exc

    def complete(self, owner_id: str, task_id: str, now: datetime | None = None) -> TaskRead:
        moment = now or datetime.now(UTC)
        if moment.tzinfo is None:
            raise ValidationError("A data de conclusão deve incluir fuso horário.")
        with session_scope(self.session_factory) as session:
            task = self._required(TaskRepository(session), owner_id, task_id)
            if task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.COMPLETED
                task.completed_at = moment.astimezone(UTC)
                task.updated_at = moment.astimezone(UTC)
            result = TaskRead.model_validate(task)
        logger.info("task_completed owner=%s task=%s", owner_id, task_id)
        return result

    def reopen(self, owner_id: str, task_id: str) -> TaskRead:
        with session_scope(self.session_factory) as session:
            task = self._required(TaskRepository(session), owner_id, task_id)
            if task.status != TaskStatus.PENDING or task.completed_at is not None:
                task.status = TaskStatus.PENDING
                task.completed_at = None
                task.updated_at = datetime.now(UTC)
            result = TaskRead.model_validate(task)
        logger.info("task_reopened owner=%s task=%s", owner_id, task_id)
        return result

    def delete(self, owner_id: str, task_id: str) -> None:
        with session_scope(self.session_factory) as session:
            repository = TaskRepository(session)
            repository.delete(self._required(repository, owner_id, task_id))
        logger.info("task_deleted owner=%s task=%s", owner_id, task_id)

    @staticmethod
    def is_overdue(task: TaskRead, now: datetime | None = None) -> bool:
        moment = now or datetime.now(UTC)
        if moment.tzinfo is None:
            raise ValidationError("A data de referência deve incluir fuso horário.")
        return (
            task.status == TaskStatus.PENDING
            and task.due_at is not None
            and as_utc(task.due_at) < moment.astimezone(UTC)
        )

    @staticmethod
    def _required(repository: TaskRepository, owner_id: str, task_id: str) -> Task:
        task = repository.get(owner_id, task_id)
        if task is None:
            raise NotFoundError("Tarefa não encontrada.")
        return task


def task_create_from_values(**values: object) -> TaskCreate:
    """Converte erros Pydantic em erro de domínio amigável para adaptadores."""
    try:
        return TaskCreate.model_validate(values)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc
