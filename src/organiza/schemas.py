"""Contratos Pydantic e validações independentes da interface."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from organiza.models import TaskPriority, TaskStatus

TrimmedTitle = Annotated[str, Field(min_length=1, max_length=200)]
ShortText = Annotated[str, Field(max_length=200)]
CategoryText = Annotated[str, Field(max_length=80)]
DescriptionText = Annotated[str, Field(max_length=5000)]


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def ensure_aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        raise ValueError("Data e horário devem incluir fuso horário")
    return value


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid", str_strip_whitespace=True)


class TaskCreate(Schema):
    title: TrimmedTitle
    description: DescriptionText = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    category: CategoryText = ""
    due_at: datetime | None = None
    show_on_calendar: bool = True

    @field_validator("title", "category")
    @classmethod
    def normalize_short_text(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime | None:
        return ensure_aware(value)


class TaskUpdate(Schema):
    title: TrimmedTitle | None = None
    description: DescriptionText | None = None
    priority: TaskPriority | None = None
    category: CategoryText | None = None
    due_at: datetime | None = None
    clear_due_at: bool = False
    show_on_calendar: bool | None = None

    @field_validator("title", "category")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _normalize_text(value) if value is not None else None

    @field_validator("description")
    @classmethod
    def trim_optional_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime | None:
        return ensure_aware(value)


class TaskRead(Schema):
    id: str
    owner_id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    category: str
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    show_on_calendar: bool


class TaskQuery(Schema):
    status: TaskStatus | None = TaskStatus.PENDING
    priority: TaskPriority | None = None
    category: str | None = None
    due_from: datetime | None = None
    due_to: datetime | None = None
    search: Annotated[str, Field(max_length=200)] = ""
    order_by: str = "due_at"
    descending: bool = False

    @field_validator("due_from", "due_to")
    @classmethod
    def validate_dates(cls, value: datetime | None) -> datetime | None:
        return ensure_aware(value)


class EventCreate(Schema):
    title: TrimmedTitle
    description: DescriptionText = ""
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    location: ShortText = ""
    category: CategoryText = ""

    @field_validator("title", "location", "category")
    @classmethod
    def normalize_short_text(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("start_at", "end_at")
    @classmethod
    def validate_aware(cls, value: datetime) -> datetime:
        validated = ensure_aware(value)
        assert validated is not None
        return validated

    @model_validator(mode="after")
    def validate_interval(self) -> EventCreate:
        if self.end_at < self.start_at:
            raise ValueError("O fim do evento não pode ser anterior ao início")
        return self


class EventUpdate(Schema):
    title: TrimmedTitle | None = None
    description: DescriptionText | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    location: ShortText | None = None
    category: CategoryText | None = None

    @field_validator("title", "location", "category")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _normalize_text(value) if value is not None else None

    @field_validator("description")
    @classmethod
    def trim_optional_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("start_at", "end_at")
    @classmethod
    def validate_optional_aware(cls, value: datetime | None) -> datetime | None:
        return ensure_aware(value)


class EventRead(Schema):
    id: str
    owner_id: str
    title: str
    description: str
    start_at: datetime
    end_at: datetime
    all_day: bool
    location: str
    category: str
    created_at: datetime
    updated_at: datetime


class PreferenceUpdate(Schema):
    timezone: str
    show_completed: bool = True
    show_task_deadlines: bool = True

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Fuso horário IANA inválido") from exc
        return value


class PreferenceRead(PreferenceUpdate):
    owner_id: str


def to_utc(value: datetime) -> datetime:
    aware = ensure_aware(value)
    assert aware is not None
    return aware.astimezone(UTC)
