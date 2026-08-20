"""Entrada AppTest para páginas individuais com as dependências reais."""

import os

from organiza.auth import LOCAL_OWNER_ID
from organiza.config import get_settings
from organiza.ui.context import AppContext, get_services
from organiza.ui.pages.agenda import render_agenda
from organiza.ui.pages.dashboard import render_dashboard
from organiza.ui.pages.settings import render_settings
from organiza.ui.pages.tasks import render_tasks

settings = get_settings()
services = get_services(settings.database_url, settings.default_timezone)
context = AppContext(settings=settings, services=services, owner_id=LOCAL_OWNER_ID)

pages = {
    "dashboard": render_dashboard,
    "tasks": render_tasks,
    "agenda": render_agenda,
    "settings": render_settings,
}
pages[os.environ["ORGANIZA_TEST_PAGE"]](context)
