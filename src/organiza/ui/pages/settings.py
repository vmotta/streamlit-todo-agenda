"""Preferências do usuário e diagnóstico seguro do ambiente."""

import streamlit as st

from organiza.schemas import PreferenceUpdate
from organiza.ui.context import AppContext
from organiza.ui.shared import show_error


def render_settings(context: AppContext) -> None:
    preference = context.services.preferences.get(context.owner_id)
    st.title("Configurações")
    st.caption("Preferências salvas para sua identidade atual.")
    with st.form("preferences"):
        timezone = st.text_input(
            "Fuso horário IANA", value=preference.timezone, help="Exemplo: America/Sao_Paulo"
        )
        show_completed = st.toggle(
            "Exibir tarefas concluídas no dashboard", value=preference.show_completed
        )
        show_deadlines = st.toggle(
            "Exibir prazos de tarefas na agenda", value=preference.show_task_deadlines
        )
        submitted = st.form_submit_button("Salvar configurações", type="primary")
    if submitted:
        try:
            context.services.preferences.update(
                context.owner_id,
                PreferenceUpdate(
                    timezone=timezone,
                    show_completed=show_completed,
                    show_task_deadlines=show_deadlines,
                ),
            )
            st.success("Configurações salvas.")
            st.rerun()
        except Exception as exc:
            show_error(exc)

    st.subheader("Ambiente")
    st.write(f"**Autenticação:** {context.settings.auth_mode}")
    st.write(f"**Banco de dados:** {context.settings.database_kind}")
    if context.settings.uses_local_database:
        st.warning(
            "Este banco está em arquivo local. Em hospedagem cloud, use PostgreSQL "
            "para que os dados sobrevivam a reinicializações e novos deploys."
        )
    else:
        st.success("Persistência online configurada.")
    st.caption("Credenciais, tokens e connection strings completas nunca são exibidos.")
