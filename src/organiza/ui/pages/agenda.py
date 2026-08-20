"""Agenda visual com fallback cronológico sempre disponível."""

from datetime import UTC, datetime, timedelta

import streamlit as st

from organiza.schemas import EventRead, EventUpdate
from organiza.timeutils import localize
from organiza.ui.calendar_adapter import (
    parse_calendar_state,
    render_calendar,
    to_fullcalendar_events,
)
from organiza.ui.context import AppContext
from organiza.ui.shared import format_datetime, render_event_create_form, show_error

VIEW_OPTIONS = {
    "Mês": "dayGridMonth",
    "Semana": "timeGridWeek",
    "Dia": "timeGridDay",
}


def render_agenda(context: AppContext) -> None:
    preference = context.services.preferences.get(context.owner_id)
    timezone = preference.timezone
    st.title("Agenda")
    st.caption("[EVENTO] e [PRAZO] também diferenciam os itens sem depender apenas de cor.")

    initial_date = st.session_state.pop("agenda_initial_date", None)
    with st.expander("+ Novo evento", expanded=initial_date is not None):
        if render_event_create_form(
            context.services.events,
            context.owner_id,
            timezone,
            key="agenda-new-event",
            initial_date=initial_date,
        ):
            st.rerun()

    controls = st.columns([2, 2])
    view_label = controls[0].segmented_control("Visualização", list(VIEW_OPTIONS), default="Mês")
    include_deadlines = controls[1].toggle(
        "Mostrar prazos de tarefas", value=preference.show_task_deadlines
    )
    now = datetime.now(UTC)
    range_start, range_end = now - timedelta(days=180), now + timedelta(days=365)
    items = context.services.calendar.list_items(
        context.owner_id, range_start, range_end, include_task_deadlines=include_deadlines
    )

    visual_events = to_fullcalendar_events(items, timezone)
    state = render_calendar(visual_events, VIEW_OPTIONS[view_label or "Mês"], timezone)
    if state is None:
        st.info("Calendário visual indisponível. A lista cronológica abaixo permanece funcional.")
    else:
        _handle_calendar_action(context, parse_calendar_state(state))

    st.subheader("Lista cronológica")
    st.caption("Esta visualização acessível permanece disponível junto ao calendário visual.")
    if not items:
        st.info("Nenhum evento ou prazo no período.")
    for item in items:
        marker = "PRAZO DE TAREFA" if item.kind == "task_deadline" else "EVENTO"
        with st.container(border=True):
            st.write(f"**{marker} · {item.title}**")
            st.write(format_datetime(item.start_at, timezone, date_only=item.all_day))
            if item.description:
                st.write(item.description)
            if item.location:
                st.caption(f"Local: {item.location}")
            if item.kind == "event":
                with st.expander("Editar ou excluir evento"):
                    event = context.services.events.get(context.owner_id, item.id)
                    _render_event_edit_form(context, event, timezone)


def _handle_calendar_action(context: AppContext, action: object) -> None:
    from organiza.ui.calendar_adapter import CalendarAction

    if not isinstance(action, CalendarAction):
        return
    if action.kind == "date_click" and action.start_at:
        st.session_state["agenda_initial_date"] = action.start_at.date()
        st.rerun()
    if action.kind == "click" and action.entity_kind == "event" and action.entity_id:
        st.info("Evento selecionado. Use a lista cronológica para editar ou excluir.")
    if (
        action.kind == "change"
        and action.entity_kind == "event"
        and action.entity_id
        and action.start_at
        and action.end_at
    ):
        try:
            context.services.events.reschedule(
                context.owner_id, action.entity_id, action.start_at, action.end_at
            )
            st.success("Evento reagendado.")
            st.rerun()
        except Exception as exc:
            show_error(exc)


def _render_event_edit_form(context: AppContext, event: EventRead, timezone: str) -> None:
    start = localize(event.start_at, timezone)
    end = localize(event.end_at, timezone)
    display_end_date = (end - timedelta(days=1)).date() if event.all_day else end.date()
    with st.form(f"edit-event-{event.id}"):
        title = st.text_input("Título *", value=event.title, max_chars=200)
        description = st.text_area("Descrição", value=event.description, max_chars=5000)
        all_day = st.checkbox("Evento de dia inteiro", value=event.all_day)
        date_columns = st.columns(2)
        start_date = date_columns[0].date_input("Data inicial", value=start.date())
        end_date = date_columns[1].date_input("Data final", value=display_end_date)
        if all_day:
            start_time, end_time = datetime.min.time(), datetime.min.time()
        else:
            time_columns = st.columns(2)
            start_time = time_columns[0].time_input("Início", value=start.time())
            end_time = time_columns[1].time_input("Fim", value=end.time())
        detail_columns = st.columns(2)
        location = detail_columns[0].text_input("Local", value=event.location, max_chars=200)
        category = detail_columns[1].text_input("Categoria", value=event.category, max_chars=80)
        submitted = st.form_submit_button("Salvar alterações")
    if submitted:
        from organiza.ui.shared import local_datetime

        start_at = local_datetime(start_date, start_time, timezone)
        end_day = end_date + timedelta(days=1) if all_day else end_date
        end_at = local_datetime(end_day, end_time, timezone)
        try:
            context.services.events.update(
                context.owner_id,
                event.id,
                EventUpdate(
                    title=title,
                    description=description,
                    start_at=start_at,
                    end_at=end_at,
                    all_day=all_day,
                    location=location,
                    category=category,
                ),
            )
            st.success("Evento atualizado.")
            st.rerun()
        except Exception as exc:
            show_error(exc)
    st.divider()
    confirmed = st.checkbox("Confirmo a exclusão deste evento", key=f"confirm-event-{event.id}")
    if st.button("Excluir evento", key=f"delete-event-{event.id}", disabled=not confirmed):
        context.services.events.delete(context.owner_id, event.id)
        st.rerun()
