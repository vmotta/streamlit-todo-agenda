"""Modelos SQLAlchemy e constraints do banco."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Enum, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from organiza.db_types import UTCDateTime


def utc_now() -> datetime:
    from datetime import UTC

    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TaskStatus(enum.StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


class TaskPriority(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, onupdate=utc_now)


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_tasks_title_not_blank"),
        Index("ix_tasks_owner_status", "owner_id", "status"),
        Index("ix_tasks_owner_due", "owner_id", "due_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, values_callable=lambda e: [item.value for item in e]),
        default=TaskStatus.PENDING,
        index=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, native_enum=False, values_callable=lambda e: [item.value for item in e]),
        default=TaskPriority.MEDIUM,
    )
    category: Mapped[str] = mapped_column(String(80), default="")
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    show_on_calendar: Mapped[bool] = mapped_column(Boolean, default=True)


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_events_title_not_blank"),
        CheckConstraint("end_at >= start_at", name="ck_events_end_after_start"),
        Index("ix_events_owner_start", "owner_id", "start_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    start_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str] = mapped_column(String(80), default="")


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    owner_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    timezone: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo")
    show_completed: Mapped[bool] = mapped_column(Boolean, default=True)
    show_task_deadlines: Mapped[bool] = mapped_column(Boolean, default=True)
