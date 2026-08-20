"""Dependências compartilhadas pela UI sem sessão mutável global."""

from dataclasses import dataclass

import streamlit as st
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from organiza.config import Settings
from organiza.db import build_database
from organiza.services.calendar import CalendarService
from organiza.services.dashboard import DashboardService
from organiza.services.events import EventService
from organiza.services.preferences import PreferenceService
from organiza.services.tasks import TaskService


@dataclass(frozen=True)
class Services:
    engine: Engine
    session_factory: sessionmaker[Session]
    tasks: TaskService
    events: EventService
    preferences: PreferenceService
    dashboard: DashboardService
    calendar: CalendarService


@dataclass(frozen=True)
class AppContext:
    settings: Settings
    services: Services
    owner_id: str


@st.cache_resource(show_spinner="Preparando banco de dados…")
def get_services(database_url: str, default_timezone: str) -> Services:
    settings = Settings(database_url=database_url, default_timezone=default_timezone)
    engine, factory = build_database(settings)
    return Services(
        engine=engine,
        session_factory=factory,
        tasks=TaskService(factory),
        events=EventService(factory),
        preferences=PreferenceService(factory, default_timezone),
        dashboard=DashboardService(factory),
        calendar=CalendarService(factory),
    )
