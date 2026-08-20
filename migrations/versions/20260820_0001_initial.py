"""Cria tarefas, eventos e preferências.

Revision ID: 20260820_0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(9), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(6), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(80), nullable=False, server_default=""),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("show_on_calendar", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_tasks_title_not_blank"),
        sa.CheckConstraint("status IN ('pending', 'completed')", name="ck_tasks_status"),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_tasks_priority"),
    )
    op.create_index("ix_tasks_owner_id", "tasks", ["owner_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])
    op.create_index("ix_tasks_owner_status", "tasks", ["owner_id", "status"])
    op.create_index("ix_tasks_owner_due", "tasks", ["owner_id", "due_at"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("location", sa.String(200), nullable=False, server_default=""),
        sa.Column("category", sa.String(80), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_events_title_not_blank"),
        sa.CheckConstraint("end_at >= start_at", name="ck_events_end_after_start"),
    )
    op.create_index("ix_events_owner_id", "events", ["owner_id"])
    op.create_index("ix_events_start_at", "events", ["start_at"])
    op.create_index("ix_events_owner_start", "events", ["owner_id", "start_at"])

    op.create_table(
        "user_preferences",
        sa.Column("owner_id", sa.String(255), primary_key=True),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="America/Sao_Paulo"),
        sa.Column("show_completed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("show_task_deadlines", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_index("ix_events_owner_start", table_name="events")
    op.drop_index("ix_events_start_at", table_name="events")
    op.drop_index("ix_events_owner_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_tasks_owner_due", table_name="tasks")
    op.drop_index("ix_tasks_owner_status", table_name="tasks")
    op.drop_index("ix_tasks_due_at", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_owner_id", table_name="tasks")
    op.drop_table("tasks")
