# Architecture

## Layers

```text
main ──► api ──► services ──► domain
              └─► adapters ──► domain
```

| Layer | Holds | May import | Must not import |
|---|---|---|---|
| `main` | The composition root: builds the app, wires layers | everything | |
| `api` | Routes, request and response models, error format | services, domain | adapters |
| `services` | Use cases; the ports (interfaces) they need | domain | api, adapters, the web framework |
| `domain` | Business rules as plain Python | the standard library | api, services, adapters, settings, any framework or storage library |
| `adapters` | Database, queue and client code that implements a port (`sql.py` is the SQLAlchemy one; `memory.py` is for tests) | domain, services (for the port types) | api |

`make structure-check` fails when an import breaks these rules.

## Rules

- A route parses input, calls one service method and shapes the response. Rules do
  not live in routes.
- A service depends on a port (a `Protocol`) it defines, not on a concrete adapter.
  `main.py` chooses the adapter.
- API models and domain types are separate; convert at the edge.
- Errors leave the service as domain exceptions; `api/errors.py` turns them into
  problem-details responses.
- Add a feature as a new module in each layer (for example `items`), not as a new
  layer. When a feature grows, group by feature: `items/api.py`, `items/service.py`.
- Settings are read once in `settings.py` and passed in (see the Settings class and
  `.env.example`; `make check-env` keeps them in step with the cluster config).

## Storage and migrations

- `adapters/sql.py` is the only code that knows the table layout. Tests use
  `adapters/memory.py` and one SQLite file test that runs the real migrations.
- The schema changes only through migrations in `migrations/versions/`, which ship inside
  the package. Run them with `python -m {{package}}.migrate`: Compose does it as a one-shot
  service, a cluster as a Job that gets the database URL and no other secret
  (`MigrationSettings`). Make every migration backward compatible with the previous
  release (see the database-migrations skill).
- Readiness (`/readyz`) pings the database; liveness (`/healthz`) checks nothing else.

## Decisions

Record significant choices as short decision records in `docs/decisions/` (see the
architecture-decisions skill).
