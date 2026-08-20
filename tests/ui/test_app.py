from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from organiza.config import clear_settings_cache
from organiza.ui.context import get_services

APP = Path(__file__).parents[2] / "streamlit_app.py"


@pytest.fixture
def app_test(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'ui.db').as_posix()}")
    monkeypatch.setenv("AUTH_MODE", "none")
    monkeypatch.setenv("ENVIRONMENT", "test")
    clear_settings_cache()
    get_services.clear()
    app = AppTest.from_file(str(APP), default_timeout=15)
    app.run()
    return app


def test_application_loads_empty_dashboard(app_test: AppTest) -> None:
    assert not app_test.exception
    assert app_test.title[0].value == "Organiza"
    assert any("Nada agendado" in item.value for item in app_test.info)
    assert [metric.label for metric in app_test.metric] == [
        "Pendentes",
        "Atrasadas",
        "Para hoje",
        "Eventos hoje",
    ]
