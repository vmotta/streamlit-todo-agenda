"""Composição de eventos e prazos sem duplicação no banco."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session, sessionmaker

from organiza.db import session_scope
from organiza.repositories.events import EventRepository
from organiza.repositories.tasks import TaskRepository
from organiza.timeutils import as_utc


@dataclass(frozen=True)
class CalendarItem:
    id: str
    kind: Literal["event", "task_deadline"]
    title: str
    start_at: datetime
    end_at: datetime | None
    all_day: bool
    description: str = ""
    location: str = ""


class CalendarService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def list_items(
        self,
        owner_id: str,
        start: datetime,
        end: datetime,
        include_task_deadlines: bool = True,
    ) -> list[CalendarItem]:
        with session_scope(self.session_factory) as session:
            events = EventRepository(session).list_between(owner_id, start, end)
            result = [
                CalendarItem(
                    id=item.id,
                    kind="event",
                    title=item.title,
                    start_at=as_utc(item.start_at),
                    end_at=as_utc(item.end_at),
                    all_day=item.all_day,
                    description=item.description,
                    location=item.location,
                )
                for item in events
            ]
            if include_task_deadlines:
                tasks = TaskRepository(session).due_between(owner_id, start, end)
                for item in tasks:
                    if item.due_at is None:
                        continue
                    result.append(
                        CalendarItem(
                            id=item.id,
                            kind="task_deadline",
                            title=item.title,
                            start_at=as_utc(item.due_at),
                            end_at=None,
                            all_day=False,
                            description=item.description,
                        )
                    )
        return sorted(result, key=lambda item: item.start_at)
