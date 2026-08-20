"""Configuração tipada da aplicação, carregada apenas do ambiente."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
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

    def ensure_local_data_directory(self) -> None:
        if not self.database_url.startswith("sqlite:///"):
            return
        raw_path = self.database_url.removeprefix("sqlite:///")
        if raw_path == ":memory:" or raw_path.startswith("file:"):
            return
        Path(raw_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
