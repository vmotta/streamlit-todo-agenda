from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select

from organiza.config import clear_settings_cache
from organiza.db import create_db_engine, create_session_factory, session_scope
from organiza.models import Task
from organiza.schemas import TaskCreate
from organiza.services.tasks import TaskService


def test_data_survives_engine_restart(tmp_path: Path) -> None:
    database = tmp_path / "persistent.db"
    url = f"sqlite:///{database.as_posix()}"
    first_engine = create_db_engine(url)
    from organiza.db import initialize_database

    initialize_database(first_engine)
    task = TaskService(create_session_factory(first_engine)).create(
        "alice", TaskCreate(title="Persistente")
    )
    first_engine.dispose()

    second_engine = create_db_engine(url)
    loaded = TaskService(create_session_factory(second_engine)).get("alice", task.id)
    second_engine.dispose()
    assert loaded.title == "Persistente"


def test_initial_migration_builds_expected_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "migration.db"
    url = f"sqlite:///{database.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    clear_settings_cache()
    config = Config("alembic.ini")
    config.set_main_option("script_location", str(Path("migrations").resolve()))
    command.upgrade(config, "head")

    engine = create_db_engine(url)
    assert {"tasks", "events", "user_preferences", "alembic_version"}.issubset(
        inspect(engine).get_table_names()
    )
    engine.dispose()
    clear_settings_cache()


def test_session_scope_rolls_back_on_error(session_factory: object) -> None:
    with pytest.raises(RuntimeError):  # noqa: SIM117
        with session_scope(session_factory) as session:  # type: ignore[arg-type]
            session.add(
                Task(
                    owner_id="alice",
                    title="Não persistir",
                    due_at=datetime(2026, 8, 20, tzinfo=UTC),
                )
            )
            raise RuntimeError("rollback")
    with session_scope(session_factory) as session:  # type: ignore[arg-type]
        assert session.scalar(select(Task)) is None
