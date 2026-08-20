"""CRUD, pesquisa, filtros e ordenação de tarefas."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from organiza.models import TaskStatus
from organiza.schemas import TaskQuery, TaskUpdate
from organiza.timeutils import local_day_bounds, localize
from organiza.ui.context import AppContext
from organiza.ui.shared import (
    PRIORITY_LABELS,
    format_datetime,
    local_datetime,
    render_task_create_form,
    show_error,
)

STATUS_OPTIONS = {
    "Pendentes": TaskStatus.PENDING,
    "Concluídas": TaskStatus.COMPLETED,
    "Todas": None,
}
ORDER_OPTIONS = {
    "Prazo": "due_at",
    "Prioridade": "priority",
    "Criação": "created_at",
    "Título": "title",
}


def render_tasks(context: AppContext) -> None:
    preference = context.services.preferences.get(context.owner_id)
    timezone = preference.timezone
    st.title("Tarefas")
    st.caption("Concluir uma tarefa leva um clique. E toda alteração fica persistida.")

    with st.expander("+ Nova tarefa", expanded=False):
        if render_task_create_form(
            context.services.tasks, context.owner_id, timezone, key="tasks-new-task"
        ):
            st.rerun()

    categories = context.services.tasks.categories(context.owner_id)
    with st.container(border=True):
        search = st.text_input("Pesquisar", placeholder="Título, descrição ou categoria")
        row1 = st.columns(3)
        status_label = row1[0].selectbox("Status", list(STATUS_OPTIONS), index=0)
        priority_label = row1[1].selectbox("Prioridade", ["Todas", *PRIORITY_LABELS.values()])
        category = row1[2].selectbox("Categoria", ["Todas", *categories])
        row2 = st.columns(3)
        due_filter = row2[0].selectbox(
            "Prazo", ["Qualquer", "Atrasadas", "Hoje", "Próximos 7 dias", "Sem prazo"]
        )
        order_label = row2[1].selectbox("Ordenar por", list(ORDER_OPTIONS))
        descending = row2[2].toggle("Ordem decrescente", value=False)

    query = _build_query(
        status_label,
        priority_label,
        category,
        due_filter,
        search,
        ORDER_OPTIONS[order_label],
        descending,
        timezone,
    )
    tasks = context.services.tasks.list(context.owner_id, query)
    if due_filter == "Sem prazo":
        tasks = [item for item in tasks if item.due_at is None]

    st.subheader(f"{len(tasks)} tarefa{'s' if len(tasks) != 1 else ''}")
    if not tasks:
        st.info("Nenhuma tarefa corresponde aos filtros atuais.")
    for task in tasks:
        _render_task_card(context, task, timezone)


def _build_query(
    status_label: str,
    priority_label: str,
    category: str,
    due_filter: str,
    search: str,
    order_by: str,
    descending: bool,
    timezone: str,
) -> TaskQuery:
    priority = next(
        (item for item, label in PRIORITY_LABELS.items() if label == priority_label), None
    )
    due_from = due_to = None
    now = datetime.now(UTC)
    today_start, tomorrow_start = local_day_bounds(
        now.astimezone(ZoneInfo(timezone)).date(), timezone
    )
    if due_filter == "Atrasadas":
        due_to = now
    elif due_filter == "Hoje":
        due_from, due_to = today_start, tomorrow_start
    elif due_filter == "Próximos 7 dias":
        due_from, due_to = now, tomorrow_start + timedelta(days=6)
    return TaskQuery(
        status=STATUS_OPTIONS[status_label],
        priority=priority,
        category=None if category == "Todas" else category,
        due_from=due_from,
        due_to=due_to,
        search=search,
        order_by=order_by,
        descending=descending,
    )


def _render_task_card(context: AppContext, task: object, timezone: str) -> None:
    from organiza.schemas import TaskRead

    assert isinstance(task, TaskRead)
    overdue = context.services.tasks.is_overdue(task)
    with st.container(border=True):
        title_col, action_col = st.columns([4, 1])
        title_col.subheader(task.title)
        if task.status == TaskStatus.PENDING:
            if action_col.button("Concluir", key=f"complete-{task.id}", type="primary"):
                context.services.tasks.complete(context.owner_id, task.id)
                st.rerun()
        elif action_col.button("Reabrir", key=f"reopen-{task.id}"):
            context.services.tasks.reopen(context.owner_id, task.id)
            st.rerun()
        labels = [f"Prioridade: {PRIORITY_LABELS[task.priority]}"]
        if task.category:
            labels.append(f"Categoria: {task.category}")
        if overdue:
            labels.append("ATRASADA")
        st.caption(" · ".join(labels))
        st.write(f"**Prazo:** {format_datetime(task.due_at, timezone)}")
        if task.description:
            st.write(task.description)
        with st.expander("Editar ou excluir"):
            _render_task_edit_form(context, task, timezone)
            st.divider()
            confirmed = st.checkbox("Confirmo a exclusão desta tarefa", key=f"confirm-{task.id}")
            if st.button(
                "Excluir tarefa", key=f"delete-{task.id}", disabled=not confirmed, type="secondary"
            ):
                context.services.tasks.delete(context.owner_id, task.id)
                st.rerun()


def _render_task_edit_form(context: AppContext, task: object, timezone: str) -> None:
    from organiza.schemas import TaskRead

    assert isinstance(task, TaskRead)
    due_local = localize(task.due_at, timezone) if task.due_at else None
    with st.form(f"edit-task-{task.id}"):
        title = st.text_input("Título *", value=task.title, max_chars=200)
        description = st.text_area("Descrição", value=task.description, max_chars=5000)
        columns = st.columns(2)
        priority_label = columns[0].selectbox(
            "Prioridade",
            list(PRIORITY_LABELS.values()),
            index=list(PRIORITY_LABELS).index(task.priority),
        )
        category = columns[1].text_input("Categoria", value=task.category, max_chars=80)
        has_due = st.checkbox("Definir prazo", value=due_local is not None)
        due_at = None
        if has_due:
            due_columns = st.columns(2)
            due_date = due_columns[0].date_input(
                "Data (DD/MM/AAAA)", value=due_local.date() if due_local else date.today()
            )
            due_time = due_columns[1].time_input(
                "Horário (24h)", value=due_local.time() if due_local else time(18, 0)
            )
            due_at = local_datetime(due_date, due_time, timezone)
        show_on_calendar = st.checkbox(
            "Mostrar prazo na agenda", value=task.show_on_calendar, disabled=not has_due
        )
        submitted = st.form_submit_button("Salvar alterações")
    if submitted:
        priority = next(item for item, label in PRIORITY_LABELS.items() if label == priority_label)
        try:
            context.services.tasks.update(
                context.owner_id,
                task.id,
                TaskUpdate(
                    title=title,
                    description=description,
                    priority=priority,
                    category=category,
                    due_at=due_at,
                    clear_due_at=not has_due,
                    show_on_calendar=show_on_calendar if has_due else False,
                ),
            )
            st.success("Tarefa atualizada.")
            st.rerun()
        except Exception as exc:
            show_error(exc)
