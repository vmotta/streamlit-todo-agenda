"""Casos de uso de eventos, inclusive alterações originadas pelo calendário."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from organiza.db import session_scope
from organiza.exceptions import NotFoundError, PersistenceError, ValidationError
from organiza.models import Event
from organiza.repositories.events import EventRepository
from organiza.schemas import EventCreate, EventRead, EventUpdate, to_utc
from organiza.timeutils import as_utc

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create(self, owner_id: str, data: EventCreate) -> EventRead:
        values = data.model_dump()
        values["start_at"] = to_utc(data.start_at)
        values["end_at"] = to_utc(data.end_at)
        event = Event(owner_id=owner_id, **values)
        try:
            with session_scope(self.session_factory) as session:
                result = EventRead.model_validate(EventRepository(session).add(event))
            logger.info("event_created owner=%s event=%s", owner_id, result.id)
            return result
        except SQLAlchemyError as exc:
            logger.error("event_create_failed owner=%s", owner_id, exc_info=True)
            raise PersistenceError("Não foi possível salvar o evento.") from exc

    def get(self, owner_id: str, event_id: str) -> EventRead:
        with session_scope(self.session_factory) as session:
            return EventRead.model_validate(
                self._required(EventRepository(session), owner_id, event_id)
            )

    def list_between(self, owner_id: str, start: datetime, end: datetime) -> list[EventRead]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValidationError("O período deve incluir fuso horário.")
        if end < start:
            raise ValidationError("O fim do período não pode ser anterior ao início.")
        with session_scope(self.session_factory) as session:
            events = EventRepository(session).list_between(owner_id, to_utc(start), to_utc(end))
            return [EventRead.model_validate(item) for item in events]

    def upcoming(self, owner_id: str, moment: datetime, limit: int = 8) -> list[EventRead]:
        if moment.tzinfo is None:
            raise ValidationError("A data de referência deve incluir fuso horário.")
        with session_scope(self.session_factory) as session:
            events = EventRepository(session).upcoming(owner_id, to_utc(moment), limit)
            return [EventRead.model_validate(item) for item in events]

    def update(self, owner_id: str, event_id: str, data: EventUpdate) -> EventRead:
        try:
            with session_scope(self.session_factory) as session:
                event = self._required(EventRepository(session), owner_id, event_id)
                changes = data.model_dump(exclude_unset=True)
                start = changes.get("start_at", as_utc(event.start_at))
                end = changes.get("end_at", as_utc(event.end_at))
                if not isinstance(start, datetime) or not isinstance(end, datetime):
                    raise ValidationError("Início e fim do evento são obrigatórios.")
                validated = EventCreate(
                    title=str(changes.get("title", event.title)),
                    description=str(changes.get("description", event.description)),
                    start_at=start,
                    end_at=end,
                    all_day=bool(changes.get("all_day", event.all_day)),
                    location=str(changes.get("location", event.location)),
                    category=str(changes.get("category", event.category)),
                )
                normalized = validated.model_dump()
                normalized["start_at"] = to_utc(validated.start_at)
                normalized["end_at"] = to_utc(validated.end_at)
                for field, value in normalized.items():
                    setattr(event, field, value)
                session.flush()
                result = EventRead.model_validate(event)
            logger.info("event_updated owner=%s event=%s", owner_id, event_id)
            return result
        except SQLAlchemyError as exc:
            logger.error("event_update_failed owner=%s event=%s", owner_id, event_id, exc_info=True)
            raise PersistenceError("Não foi possível atualizar o evento.") from exc

    def reschedule(
        self, owner_id: str, event_id: str, start_at: datetime, end_at: datetime
    ) -> EventRead:
        """Entrada única para drag-and-drop e redimensionamento."""
        return self.update(owner_id, event_id, EventUpdate(start_at=start_at, end_at=end_at))

    def delete(self, owner_id: str, event_id: str) -> None:
        with session_scope(self.session_factory) as session:
            repository = EventRepository(session)
            repository.delete(self._required(repository, owner_id, event_id))
        logger.info("event_deleted owner=%s event=%s", owner_id, event_id)

    @staticmethod
    def _required(repository: EventRepository, owner_id: str, event_id: str) -> Event:
        event = repository.get(owner_id, event_id)
        if event is None:
            raise NotFoundError("Evento não encontrado.")
        return event
