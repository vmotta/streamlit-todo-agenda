"""Configuração tipada da aplicação, carregada do ambiente ou de secrets."""

from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "sqlite:///./data/organiza.db"


class Settings(BaseSettings):
    """Configuração segura e independente da UI."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "Organiza"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = DEFAULT_DATABASE_URL
    auth_mode: Literal["none", "oidc"] = "none"
    default_timezone: str = "America/Sao_Paulo"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> str:
        """Aceita URLs PostgreSQL comuns e seleciona explicitamente psycopg 3."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("DATABASE_URL não pode ser vazia")
        normalized = value.strip()
        if normalized.startswith("postgres://"):
            return normalized.replace("postgres://", "postgresql+psycopg://", 1)
        if normalized.startswith("postgresql://"):
            return normalized.replace("postgresql://", "postgresql+psycopg://", 1)
        return normalized

    @field_validator("default_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Fuso horário IANA inválido") from exc
        return value

    @property
    def database_kind(self) -> str:
        if self.database_url.startswith("sqlite"):
            return "SQLite"
        if self.database_url.startswith("postgresql"):
            return "PostgreSQL"
        return "Outro"

    @property
    def safe_database_url(self) -> str:
        """URL sanitizada para diagnóstico sem expor credenciais."""
        if self.database_url.startswith("sqlite"):
            return "sqlite:///…/organiza.db"
        parts = urlsplit(self.database_url)
        host = parts.hostname or "host"
        port = f":{parts.port}" if parts.port else ""
        return urlunsplit((parts.scheme, f"***@{host}{port}", parts.path, "", ""))

    @property
    def uses_local_database(self) -> bool:
        """Indica armazenamento em arquivo local, não durável em hosts efêmeros."""
        return self.database_url.startswith("sqlite")

    def ensure_local_data_directory(self) -> None:
        if not self.database_url.startswith("sqlite:///"):
            return
        raw_path = self.database_url.removeprefix("sqlite:///")
        if raw_path == ":memory:" or raw_path.startswith("file:"):
            return
        Path(raw_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def load_settings(overrides: Mapping[str, object] | None = None) -> Settings:
    """Combina ambiente com chaves raiz de um provedor de secrets.

    Argumentos explícitos têm precedência sobre variáveis de ambiente. Chaves
    desconhecidas e seções aninhadas, como ``[auth]``, são ignoradas.
    """
    allowed_fields = Settings.model_fields
    init_values: dict[str, Any] = {}
    for key, value in (overrides or {}).items():
        field_name = str(key).lower()
        if field_name in allowed_fields:
            init_values[field_name] = value
    return Settings(**init_values)


def clear_settings_cache() -> None:
    get_settings.cache_clear()
