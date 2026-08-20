# Organiza

Aplicação pessoal de produtividade em Python e Streamlit para gerenciar tarefas, conclusões e eventos em uma agenda persistente. A interface é pt-BR, usa datas `DD/MM/AAAA`, horários de 24 horas e adota `America/Sao_Paulo` como fuso padrão configurável.

## Funcionalidades

- Tarefas: criar, editar, excluir, concluir de forma idempotente, reabrir, pesquisar, filtrar e ordenar.
- Prioridade, categoria, descrição, prazo e indicador textual `ATRASADA`.
- Eventos: criar, editar, excluir e reagendar com validação única na camada de serviços.
- Agenda mensal, semanal e diária baseada em FullCalendar, mais lista cronológica sempre disponível.
- Prazos de tarefas compostos em leitura, sem duplicação na tabela de eventos, identificados como `[PRAZO]`.
- Dashboard com hoje, atrasadas, próximos eventos e concluídas recentemente.
- Preferências persistentes por usuário para fuso e opções de exibição.
- SQLite local ou PostgreSQL por `DATABASE_URL`.
- Modo local sem login ou autenticação OIDC nativa do Streamlit.
- Migrações Alembic, testes automatizados, lint, type check, auditoria, CI e container não-root.

## Arquitetura

```text
streamlit_app.py             ponto de entrada, autenticação e st.navigation
src/organiza/
├── config.py                configuração Pydantic
├── db.py                    engine, WAL/busy_timeout e sessões curtas
├── models.py                modelos e constraints SQLAlchemy
├── schemas.py               contratos e validações Pydantic
├── repositories/            consultas sempre filtradas por owner_id
├── services/                regras de negócio e transações
└── ui/                      páginas e adaptador FullCalendar
migrations/                  histórico Alembic
tests/                       unitários, integração e AppTest
```

A UI depende dos serviços; os serviços controlam regras e transações; os repositórios isolam a persistência. Nenhuma regra essencial depende de `st.session_state` ou do componente de calendário.

## Versões de referência

- Python: `>=3.12,<3.15` (desenvolvimento validado também com 3.14.7; imagem Docker 3.12).
- uv: 0.12.5 no ambiente de validação.
- Streamlit: 1.60.0.
- SQLAlchemy: 2.0.52.
- Alembic: 1.19.1.
- Pydantic: 2.13.4.
- streamlit-calendar: 1.4.0.

As dependências transitivas ficam integralmente travadas em `uv.lock`.

## Instalação local

Pré-requisitos: Python 3.12+ e [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone <URL_DO_REPOSITORIO>
cd streamlit-todo-agenda
cp .env.example .env
uv sync --frozen
uv run alembic upgrade head
uv run streamlit run streamlit_app.py
```

No PowerShell, substitua `cp` por:

```powershell
Copy-Item .env.example .env
```

Acesse `http://localhost:8501`. No modo local, a identidade fixa e não editável é `local-user`.

### SQLite

O padrão é `sqlite:///./data/organiza.db`. O diretório, banco e arquivos WAL não entram no Git. A conexão ativa foreign keys, `busy_timeout=5000` e WAL para reduzir contenção local.

### PostgreSQL

Defina no ambiente, sem registrar a credencial:

```bash
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/organiza
uv run alembic upgrade head
uv run streamlit run streamlit_app.py
```

As telas mostram apenas o tipo do banco, nunca a URL completa.

## Migrações

Aplicar todas:

```bash
uv run alembic upgrade head
```

Criar uma revisão depois de alterar os modelos:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Revise manualmente toda migração autogerada antes de commitá-la.

## Autenticação OIDC

1. Defina `AUTH_MODE=oidc`.
2. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`.
3. Configure `redirect_uri`, `cookie_secret`, `client_id`, `client_secret` e `server_metadata_url`.
4. Cadastre no provedor o callback `https://seu-host/oauth2callback`.

O `owner_id` vem exclusivamente do claim OIDC `sub`; nenhuma entrada editável controla a identidade. Usuários não autenticados não alcançam as páginas nem o banco. Consulte a [documentação oficial de autenticação do Streamlit](https://docs.streamlit.io/develop/concepts/connections/authentication).

## Qualidade e testes

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src streamlit_app.py
uv run pytest --cov=src/organiza --cov-report=term-missing --cov-report=xml --cov-fail-under=85
uv run pip-audit
```

Os testes usam bancos SQLite temporários e cobrem domínio, CRUD, persistência, filtros, isolamento entre usuários, migração, composição da agenda, dashboard e fluxos Streamlit com `AppTest`.

Para instalar os hooks locais:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Docker

```bash
docker build -t organiza:local .
docker run --rm -p 8501:8501 -v organiza-data:/app/data organiza:local
```

Ou:

```bash
docker compose up --build
```

O entrypoint aplica migrações antes de iniciar, o processo executa como usuário não-root e o healthcheck consulta `/_stcore/health`.

Para PostgreSQL em container, injete `DATABASE_URL` por secret/ambiente do orquestrador; não a grave no `compose.yaml`.

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `AUTH_MODE` | `none` | `none` ou `oidc` |
| `DATABASE_URL` | SQLite em `data/` | URL SQLAlchemy |
| `DEFAULT_TIMEZONE` | `America/Sao_Paulo` | fuso IANA inicial |
| `ENVIRONMENT` | `development` | `development`, `test` ou `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` ou `ERROR` |

## Segurança e privacidade

- Toda leitura, atualização e exclusão de tarefa/evento verifica `owner_id`.
- ORM parametrizado, limites de campo, constraints de banco e datas timezone-aware.
- Segredos, `.env`, bancos e caches estão ignorados.
- Logs registram IDs técnicos e operações, sem conteúdo das tarefas nem credenciais.
- Conteúdo do usuário é renderizado apenas por componentes seguros do Streamlit; não se usa `unsafe_allow_html=True`.
- Imagem final é mínima, não-root e auditada no CI.

Consulte [SECURITY.md](SECURITY.md) para relatar vulnerabilidades.

## Implantação

1. Provisione PostgreSQL e usuário com privilégios mínimos.
2. Configure `DATABASE_URL`, `AUTH_MODE=oidc` e secrets OIDC no ambiente.
3. Restrinja TLS no proxy/orquestrador e ajuste o callback OIDC ao host HTTPS.
4. Execute `alembic upgrade head` como etapa de release.
5. Inicie o container e monitore `/_stcore/health` e os logs estruturados por nível.
6. Faça backup e teste restauração do banco de acordo com o RPO/RTO do ambiente.

## Troubleshooting

- **Banco SQLite bloqueado:** confirme que só instâncias compatíveis compartilham o volume; WAL não torna SQLite indicado para múltiplos hosts. Use PostgreSQL em escala horizontal.
- **Falha de callback OIDC:** o `redirect_uri` deve terminar em `/oauth2callback` e ser idêntico ao cadastrado no provedor.
- **Fuso inválido:** use um nome IANA, por exemplo `America/Sao_Paulo`; o formulário rejeita valores desconhecidos.
- **Calendário visual indisponível:** a lista cronológica permanece funcional. Verifique a dependência `streamlit-calendar` e políticas de componentes do host.
- **Migração divergente:** execute `uv run alembic current` e `uv run alembic heads`; não edite um banco de produção manualmente.

## Decisões técnicas

- UUIDs textuais funcionam de forma equivalente em SQLite e PostgreSQL.
- Horários são normalizados em UTC no banco e convertidos para o fuso do usuário na leitura.
- Eventos de dia inteiro usam fim exclusivo, compatível com FullCalendar.
- Prazos são agregados à agenda em `CalendarService`, nunca copiados para `events`.
- `Base.metadata.create_all` permite a primeira inicialização local; Alembic é a fonte de evolução do schema e é executado no container.
- Não há licença definida nesta versão, conforme decisão explícita do projeto.

## Contribuição

Leia [CONTRIBUTING.md](CONTRIBUTING.md). Mudanças relevantes devem incluir teste, migração quando necessária e atualização do changelog.

