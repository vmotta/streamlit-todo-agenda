# Changelog

Todas as mudanças relevantes são registradas neste arquivo. O formato segue Keep a Changelog, sem declarar licença.

## [Não lançado]

### Alterado

- Secrets raiz do Streamlit agora configuram o ambiente explicitamente.
- URLs `postgres://` e `postgresql://` usam automaticamente o driver psycopg 3.
- A interface alerta quando produção usa SQLite temporário e confirma PostgreSQL online.

## [0.1.0] - 2026-08-20

### Adicionado

- CRUD completo e persistente de tarefas e eventos.
- Dashboard, filtros, pesquisa, ordenação e preferências.
- Agenda FullCalendar com lista acessível e composição de prazos.
- Isolamento por proprietário e modos de autenticação local/OIDC.
- Alembic, testes, qualidade, Docker, CI, CodeQL e Dependabot.

