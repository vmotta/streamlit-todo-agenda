"""Dashboard enxuto e orientado ao dia do usuário."""

from datetime import UTC, datetime

import streamlit as st

from organiza.ui.context import AppContext
from organiza.ui.shared import (
    format_datetime,
    render_event_create_form,
    render_task_create_form,
)


def render_dashboard(context: AppContext) -> None:
    preference = context.services.preferences.get(context.owner_id)
    snapshot = context.services.dashboard.snapshot(
        context.owner_id, datetime.now(UTC), preference.timezone
    )
    st.title("Organiza")
    st.caption("Seu dia, suas tarefas e sua agenda em um só lugar.")

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Pendentes", snapshot.pending_count)
    metric2.metric("Atrasadas", len(snapshot.overdue))
    metric3.metric("Para hoje", len(snapshot.tasks_today))
    metric4.metric("Eventos hoje", len(snapshot.events_today))

    create_task, create_event = st.columns(2)
    with create_task.expander("+ Nova tarefa"):
        if render_task_create_form(
            context.services.tasks, context.owner_id, preference.timezone, key="dashboard-new-task"
        ):
            st.rerun()
    with create_event.expander("+ Novo evento"):
        if render_event_create_form(
            context.services.events,
            context.owner_id,
            preference.timezone,
            key="dashboard-new-event",
        ):
            st.rerun()

    st.header("Hoje")
    if not snapshot.tasks_today and not snapshot.events_today:
        st.info("Nada agendado para hoje. Aproveite o espaço ou planeje algo novo.")
    for task in snapshot.tasks_today:
        st.write(
            f"☐ **Tarefa:** {task.title} — {format_datetime(task.due_at, preference.timezone)}"
        )
    for event in snapshot.events_today:
        st.write(
            f"▣ **Evento:** {event.title} — {format_datetime(event.start_at, preference.timezone)}"
        )

    left, right = st.columns(2)
    with left:
        st.header("Atrasadas")
        if not snapshot.overdue:
            st.caption("Nenhuma tarefa atrasada.")
        for task in snapshot.overdue:
            st.warning(
                f"**ATRASADA** · {task.title} · {format_datetime(task.due_at, preference.timezone)}"
            )
    with right:
        st.header("Próximos eventos")
        if not snapshot.upcoming_events:
            st.caption("Nenhum evento futuro.")
        for event in snapshot.upcoming_events:
            st.write(f"**{event.title}**  \n{format_datetime(event.start_at, preference.timezone)}")

    if preference.show_completed:
        st.header("Concluídas recentemente")
        if not snapshot.recently_completed:
            st.caption("As tarefas concluídas aparecerão aqui.")
        for task in snapshot.recently_completed:
            st.write(f"✓ {task.title}")
