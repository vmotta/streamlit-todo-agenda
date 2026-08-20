"""Ponto de entrada e router do Organiza."""

from __future__ import annotations

import streamlit as st

from organiza.auth import resolve_owner_id
from organiza.config import get_settings
from organiza.logging_config import configure_logging
from organiza.ui.context import AppContext, get_services
from organiza.ui.router import run_navigation


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="✅",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    claims: dict[str, object] | None = None
    if settings.auth_mode == "oidc":
        if not st.user.is_logged_in:
            st.title("Organiza")
            st.write("Entre para acessar suas tarefas e sua agenda.")
            st.button("Entrar", type="primary", on_click=st.login)
            st.stop()
        claims = dict[str, object](st.user.to_dict())
        with st.sidebar:
            name = claims.get("name") or claims.get("email") or "Usuário"
            st.caption(f"Conectado como {name}")
            st.button("Sair", on_click=st.logout)
    owner_id = resolve_owner_id(settings.auth_mode, claims)
    services = get_services(settings.database_url, settings.default_timezone)
    run_navigation(AppContext(settings=settings, services=services, owner_id=owner_id))


if __name__ == "__main__":
    main()
