"""Navegação multipágina com st.Page/st.navigation."""

from __future__ import annotations

from functools import partial

import streamlit as st

from organiza.ui.context import AppContext
from organiza.ui.pages.agenda import render_agenda
from organiza.ui.pages.dashboard import render_dashboard
from organiza.ui.pages.settings import render_settings
from organiza.ui.pages.tasks import render_tasks


def run_navigation(context: AppContext) -> None:
    pages = {
        "Organiza": [
            st.Page(
                partial(render_dashboard, context),
                title="Início",
                url_path="inicio",
                icon=":material/home:",
            ),
            st.Page(
                partial(render_tasks, context),
                title="Tarefas",
                url_path="tarefas",
                icon=":material/checklist:",
            ),
            st.Page(
                partial(render_agenda, context),
                title="Agenda",
                url_path="agenda",
                icon=":material/calendar_month:",
            ),
        ],
        "Conta": [
            st.Page(
                partial(render_settings, context),
                title="Configurações",
                url_path="configuracoes",
                icon=":material/settings:",
            )
        ],
    }
    st.navigation(pages).run()
