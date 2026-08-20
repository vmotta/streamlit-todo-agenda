"""Limpeza explícita dos recursos cacheados entre execuções AppTest."""

import gc
import os
from collections.abc import Iterator

import pytest

from organiza.ui.context import get_services


@pytest.fixture(autouse=True)
def dispose_ui_database_engine() -> Iterator[None]:
    yield
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        services = get_services(database_url, "America/Sao_Paulo")
        services.engine.dispose()
    get_services.clear()
    gc.collect()
