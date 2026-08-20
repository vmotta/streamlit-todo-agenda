"""Persistência de eventos com isolamento obrigatório por owner_id."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from organiza.models import Event


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: Event) -> Event:
        self.session.add(event)
        self.session.flush()
        self.session.refresh(event)
        return event

    def get(self, owner_id: str, event_id: str) -> Event | None:
        return self.session.scalar(
            select(Event).where(Event.id == event_id, Event.owner_id == owner_id)
        )

    def list_between(self, owner_id: str, start: datetime, end: datetime) -> list[Event]:
        return list(
            self.session.scalars(
                select(Event)
                .where(
                    Event.owner_id == owner_id,
                    Event.start_at < end,
                    Event.end_at >= start,
                )
                .order_by(Event.start_at, Event.end_at)
            )
        )

    def upcoming(self, owner_id: str, moment: datetime, limit: int = 8) -> list[Event]:
        return list(
            self.session.scalars(
                select(Event)
                .where(Event.owner_id == owner_id, Event.end_at >= moment)
                .order_by(Event.start_at)
                .limit(limit)
            )
        )

    def delete(self, event: Event) -> None:
        self.session.delete(event)
