"""Preferências persistentes por usuário."""

from sqlalchemy.orm import Session, sessionmaker

from organiza.db import session_scope
from organiza.models import UserPreference
from organiza.repositories.preferences import PreferenceRepository
from organiza.schemas import PreferenceRead, PreferenceUpdate


class PreferenceService:
    def __init__(self, session_factory: sessionmaker[Session], default_timezone: str) -> None:
        self.session_factory = session_factory
        self.default_timezone = default_timezone

    def get(self, owner_id: str) -> PreferenceRead:
        with session_scope(self.session_factory) as session:
            repository = PreferenceRepository(session)
            preference = repository.get(owner_id)
            if preference is None:
                preference = repository.add(
                    UserPreference(owner_id=owner_id, timezone=self.default_timezone)
                )
            return PreferenceRead.model_validate(preference)

    def update(self, owner_id: str, data: PreferenceUpdate) -> PreferenceRead:
        with session_scope(self.session_factory) as session:
            repository = PreferenceRepository(session)
            preference = repository.get(owner_id)
            if preference is None:
                preference = UserPreference(owner_id=owner_id)
                session.add(preference)
            for field, value in data.model_dump().items():
                setattr(preference, field, value)
            session.flush()
            return PreferenceRead.model_validate(preference)
