# Contribuindo

## Preparação

1. Instale Python 3.12+ e uv.
2. Execute `uv sync --frozen`.
3. Copie `.env.example` para `.env`.
4. Execute `uv run alembic upgrade head`.
5. Instale os hooks com `uv run pre-commit install`.

## Fluxo

- Crie uma branch curta e focada.
- Não versione bancos, secrets, `.env` ou ambientes virtuais.
- Mantenha regras de negócio em `services/`, persistência em `repositories/` e UI em `ui/`.
- Preserve o filtro de `owner_id` em toda operação.
- Inclua migração para mudanças de schema.
- Inclua testes que demonstrem comportamento, falha e isolamento.

Antes de abrir um pull request:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src streamlit_app.py
uv run pytest --cov=src/organiza --cov-fail-under=85
uv run pip-audit
```

Commits devem ser pequenos, lógicos e preferencialmente seguir Conventional Commits.

