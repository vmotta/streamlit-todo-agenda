"""Ponto de entrada e router do Organiza."""

from __future__ import annotations

import streamlit as st

from organiza.auth import resolve_owner_id
from organiza.config import Settings, get_settings, load_settings
from organiza.logging_config import configure_logging
from organiza.ui.context import AppContext, get_services
from organiza.ui.router import run_navigation


def load_app_settings() -> Settings:
    """Lê secrets raiz no Cloud e mantém variáveis de ambiente como fallback."""
    try:
        return load_settings(dict(st.secrets))
    except FileNotFoundError:
        return get_settings()


def main() -> None:
    settings = load_app_settings()
    configure_logging(settings.log_level)
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="✅",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if settings.environment == "production" and settings.uses_local_database:
        st.warning(
            "O SQLite local pode ser apagado pelo provedor de hospedagem. "
            "Configure DATABASE_URL com PostgreSQL nos Secrets para persistência online.",
            icon="⚠️",
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
