"""Criação de engine e sessões curtas/transacionais."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from organiza.config import Settings
from organiza.models import Base


def create_db_engine(database_url: str) -> Engine:
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        in_memory = database_url.endswith(":memory:")
        if not in_memory:
            path = database_url.removeprefix("sqlite:///")
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            poolclass=StaticPool if in_memory else NullPool,
            connect_args=connect_args,
        )
    else:
        engine = create_engine(database_url, pool_pre_ping=True)

    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def configure_sqlite(dbapi_connection: object, _connection_record: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            if not database_url.endswith(":memory:"):
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def initialize_database(engine: Engine) -> None:
    """Inicializa instalações novas; Alembic evolui instalações existentes."""
    Base.metadata.create_all(engine)


def build_database(settings: Settings) -> tuple[Engine, sessionmaker[Session]]:
    settings.ensure_local_data_directory()
    engine = create_db_engine(settings.database_url)
    initialize_database(engine)
    return engine, create_session_factory(engine)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        with session.begin():
            yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
