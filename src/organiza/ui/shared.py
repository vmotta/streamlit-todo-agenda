"""Componentes e conversões reutilizados pelas páginas."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from organiza.exceptions import OrganizaError
from organiza.models import TaskPriority
from organiza.schemas import EventCreate, TaskCreate
from organiza.timeutils import localize

PRIORITY_LABELS = {
    TaskPriority.LOW: "Baixa",
    TaskPriority.MEDIUM: "Média",
    TaskPriority.HIGH: "Alta",
}


def format_datetime(value: datetime | None, timezone: str, *, date_only: bool = False) -> str:
    if value is None:
        return "Sem prazo"
    localized = localize(value, timezone)
    return localized.strftime("%d/%m/%Y" if date_only else "%d/%m/%Y às %H:%M")


def local_datetime(day: date, clock: time, timezone: str) -> datetime:
    return datetime.combine(day, clock, ZoneInfo(timezone)).astimezone(UTC)


def show_error(exc: Exception) -> None:
    if isinstance(exc, OrganizaError):
        st.error(str(exc))
    elif isinstance(exc, PydanticValidationError):
        first = exc.errors()[0]
        st.error(f"Revise o formulário: {first['msg']}.")
    else:
        st.error("Ocorreu um erro inesperado. Tente novamente.")


def render_task_create_form(
    task_service: object, owner_id: str, timezone: str, *, key: str = "new-task"
) -> bool:
    from organiza.services.tasks import TaskService

    assert isinstance(task_service, TaskService)
    with st.form(key, clear_on_submit=True):
        title = st.text_input("Título *", max_chars=200, key=f"{key}-title")
        description = st.text_area("Descrição", max_chars=5000, key=f"{key}-description")
        col1, col2 = st.columns(2)
        priority_label = col1.selectbox(
            "Prioridade", list(PRIORITY_LABELS.values()), index=1, key=f"{key}-priority"
        )
        category = col2.text_input("Categoria", max_chars=80, key=f"{key}-category")
        has_due = st.checkbox("Definir prazo", key=f"{key}-has-due")
        due_at = None
        show_calendar = True
        if has_due:
            due_col1, due_col2 = st.columns(2)
            due_date = due_col1.date_input(
                "Data do prazo (DD/MM/AAAA)", value=date.today(), key=f"{key}-due-date"
            )
            due_time = due_col2.time_input(
                "Horário (24h)", value=time(18, 0), key=f"{key}-due-time"
            )
            due_at = local_datetime(due_date, due_time, timezone)
            show_calendar = st.checkbox(
                "Mostrar este prazo na agenda", value=True, key=f"{key}-show-calendar"
            )
        submitted = st.form_submit_button("Salvar tarefa", type="primary")
    if not submitted:
        return False
    priority = next(item for item, label in PRIORITY_LABELS.items() if label == priority_label)
    try:
        task_service.create(
            owner_id,
            TaskCreate(
                title=title,
                description=description,
                priority=priority,
                category=category,
                due_at=due_at,
                show_on_calendar=show_calendar,
            ),
        )
    except Exception as exc:  # Streamlit boundary: translated and logged upstream.
        show_error(exc)
        return False
    st.success("Tarefa criada.")
    return True


def render_event_create_form(
    event_service: object,
    owner_id: str,
    timezone: str,
    *,
    key: str = "new-event",
    initial_date: date | None = None,
) -> bool:
    from organiza.services.events import EventService

    assert isinstance(event_service, EventService)
    selected_date = initial_date or date.today()
    with st.form(key, clear_on_submit=True):
        title = st.text_input("Título *", max_chars=200, key=f"{key}-title")
        description = st.text_area("Descrição", max_chars=5000, key=f"{key}-description")
        all_day = st.checkbox("Evento de dia inteiro", key=f"{key}-all-day")
        start_col, end_col = st.columns(2)
        start_date = start_col.date_input(
            "Data inicial (DD/MM/AAAA)", value=selected_date, key=f"{key}-start-date"
        )
        end_date = end_col.date_input(
            "Data final (DD/MM/AAAA)", value=selected_date, key=f"{key}-end-date"
        )
        if all_day:
            start_time, end_time = time.min, time.min
        else:
            time_col1, time_col2 = st.columns(2)
            start_time = time_col1.time_input(
                "Início (24h)", value=time(9, 0), key=f"{key}-start-time"
            )
            end_time = time_col2.time_input("Fim (24h)", value=time(10, 0), key=f"{key}-end-time")
        details_col1, details_col2 = st.columns(2)
        location = details_col1.text_input("Local", max_chars=200, key=f"{key}-location")
        category = details_col2.text_input("Categoria", max_chars=80, key=f"{key}-category")
        submitted = st.form_submit_button("Salvar evento", type="primary")
    if not submitted:
        return False
    start_at = local_datetime(start_date, start_time, timezone)
    if all_day:
        end_at = local_datetime(end_date + timedelta(days=1), end_time, timezone)
    else:
        end_at = local_datetime(end_date, end_time, timezone)
    try:
        event_service.create(
            owner_id,
            EventCreate(
                title=title,
                description=description,
                start_at=start_at,
                end_at=end_at,
                all_day=all_day,
                location=location,
                category=category,
            ),
        )
    except Exception as exc:  # Streamlit boundary.
        show_error(exc)
        return False
    st.success("Evento criado.")
    return True
