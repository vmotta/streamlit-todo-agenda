from datetime import time
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from organiza.config import clear_settings_cache
from organiza.ui.context import get_services

HARNESS = Path(__file__).parent / "_page_harness.py"


def _page_app(page: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / f'{page}.db').as_posix()}")
    monkeypatch.setenv("AUTH_MODE", "none")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ORGANIZA_TEST_PAGE", page)
    clear_settings_cache()
    get_services.clear()
    return AppTest.from_file(str(HARNESS), default_timeout=15).run()


def _button(app: AppTest, label: str, occurrence: int = 0) -> Any:
    matches = [item for item in app.button if item.label == label]
    return matches[occurrence]


def _input_by_key(elements: Any, key: str) -> Any:
    return next(item for item in elements if item.key == key)


def test_task_create_complete_reopen_and_empty_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _page_app("tasks", tmp_path, monkeypatch)
    assert not app.exception
    assert any("Nenhuma tarefa" in item.value for item in app.info)

    _input_by_key(app.text_input, "tasks-new-task-title").input("Comprar leite")
    _button(app, "Salvar tarefa").click().run()
    assert not app.exception
    assert any("Comprar leite" in item.value for item in app.subheader)

    _button(app, "Concluir").click().run()
    assert not app.exception
    next(item for item in app.selectbox if item.label == "Status").select("Concluídas").run()
    assert any(item.label == "Reabrir" for item in app.button)
    _button(app, "Reabrir").click().run()
    assert not app.exception


def test_event_create_and_invalid_form(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = _page_app("agenda", tmp_path, monkeypatch)
    assert not app.exception

    _input_by_key(app.text_input, "agenda-new-event-title").input("Consulta")
    _input_by_key(app.time_input, "agenda-new-event-start-time").set_value(time(11, 0))
    _input_by_key(app.time_input, "agenda-new-event-end-time").set_value(time(10, 0))
    _button(app, "Salvar evento").click().run()
    assert app.error

    _input_by_key(app.time_input, "agenda-new-event-end-time").set_value(time(12, 0))
    _button(app, "Salvar evento").click().run()
    assert not app.exception
    assert any("EVENTO · Consulta" in item.value for item in app.markdown)


def test_settings_page_persists_timezone_and_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _page_app("settings", tmp_path, monkeypatch)
    assert not app.exception
    assert app.title[0].value == "Configurações"
    app.text_input[0].input("Europe/Lisbon")
    app.toggle[0].set_value(False)
    app.toggle[1].set_value(False)
    _button(app, "Salvar configurações").click().run()
    assert not app.exception
    assert app.text_input[0].value == "Europe/Lisbon"
    assert app.toggle[0].value is False


def test_dashboard_quick_event_and_task_forms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = _page_app("dashboard", tmp_path, monkeypatch)
    _input_by_key(app.text_input, "dashboard-new-task-title").input("Tarefa rápida")
    _button(app, "Salvar tarefa").click().run()
    assert app.metric[0].value == "1"

    _input_by_key(app.text_input, "dashboard-new-event-title").input("Evento rápido")
    _button(app, "Salvar evento").click().run()
    assert not app.exception
