"""Composição de leitura para o dashboard."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, sessionmaker

from organiza.db import session_scope
from organiza.models import TaskStatus
from organiza.repositories.events import EventRepository
from organiza.repositories.tasks import TaskRepository
from organiza.schemas import EventRead, TaskQuery, TaskRead
from organiza.timeutils import local_day_bounds


@dataclass(frozen=True)
class DashboardSnapshot:
    pending_count: int
    overdue: list[TaskRead]
    tasks_today: list[TaskRead]
    events_today: list[EventRead]
    upcoming_events: list[EventRead]
    recently_completed: list[TaskRead]


class DashboardService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def snapshot(self, owner_id: str, now: datetime, timezone: str) -> DashboardSnapshot:
        local_date = now.astimezone(ZoneInfo(timezone)).date()
        day_start, day_end = local_day_bounds(local_date, timezone)
        with session_scope(self.session_factory) as session:
            tasks = TaskRepository(session)
            events = EventRepository(session)
            pending = tasks.list(owner_id, TaskQuery(status=TaskStatus.PENDING))
            overdue = tasks.pending_before(owner_id, day_start)
            today = tasks.due_between(owner_id, day_start, day_end)
            today_events = events.list_between(owner_id, day_start, day_end)
            upcoming = events.upcoming(owner_id, now, 8)
            completed = tasks.recently_completed(owner_id, 5)
            return DashboardSnapshot(
                pending_count=len(pending),
                overdue=[TaskRead.model_validate(item) for item in overdue],
                tasks_today=[TaskRead.model_validate(item) for item in today],
                events_today=[EventRead.model_validate(item) for item in today_events],
                upcoming_events=[EventRead.model_validate(item) for item in upcoming],
                recently_completed=[TaskRead.model_validate(item) for item in completed],
            )
