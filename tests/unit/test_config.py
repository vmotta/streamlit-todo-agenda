import pytest
from pydantic import ValidationError

from organiza.config import Settings, load_settings


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://"])
def test_common_postgresql_urls_select_psycopg_driver(scheme: str) -> None:
    settings = Settings(database_url=f"{scheme}user:secret@db.example/organiza")

    assert settings.database_url == ("postgresql+psycopg://user:secret@db.example/organiza")
    assert settings.database_kind == "PostgreSQL"
    assert not settings.uses_local_database


def test_explicit_psycopg_url_is_preserved() -> None:
    url = "postgresql+psycopg://user:secret@db.example/organiza?sslmode=require"

    assert Settings(database_url=url).database_url == url


def test_root_secrets_override_environment_and_ignore_nested_sections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/fallback.db")
    settings = load_settings(
        {
            "DATABASE_URL": "postgresql://user:secret@db.example/organiza",
            "ENVIRONMENT": "production",
            "auth": {"client_id": "ignored"},
        }
    )

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.environment == "production"


def test_database_url_cannot_be_empty() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL não pode ser vazia"):
        Settings(database_url="   ")
