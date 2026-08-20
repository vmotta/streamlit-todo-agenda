"""Persistência das preferências de apresentação por usuário."""

from sqlalchemy.orm import Session

from organiza.models import UserPreference


class PreferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, owner_id: str) -> UserPreference | None:
        return self.session.get(UserPreference, owner_id)

    def add(self, preference: UserPreference) -> UserPreference:
        self.session.add(preference)
        self.session.flush()
        self.session.refresh(preference)
        return preference
