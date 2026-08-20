"""Fixtures com bancos completamente isolados."""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from organiza.db import create_db_engine, create_session_factory, initialize_database


@pytest.fixture
def db_engine(tmp_path: object) -> Iterator[Engine]:
    path = tmp_path / "test.db"  # type: ignore[operator]
    engine = create_db_engine(f"sqlite:///{path.as_posix()}")  # type: ignore[attr-defined]
    initialize_database(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(db_engine: Engine) -> sessionmaker[Session]:
    return create_session_factory(db_engine)


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 8, 20, 15, 0, tzinfo=UTC)
