# {{title}}

<one line: what this service does>

## Run locally

```bash
cp .env.example .env
docker compose up --build --wait      # app, database, migrations (python -m {{package}}.migrate)
curl http://127.0.0.1:8000/healthz
```

Without containers: `uv sync && uv run uvicorn --factory {{package}}.main:create_app --reload`
(the settings need `APP_DATABASE_URL` and `APP_API_KEY`; see `.env.example`).

## Develop

```bash
make check         # format, lint, type-check, tests, settings check
make structure-check   # layer rules (from the plugin: see docs/architecture.md)
```

## Layout

See [docs/architecture.md](docs/architecture.md). In short: `api` (HTTP) calls
`services` (use cases), which use `domain` (rules) and ports implemented by
`adapters`. `main.py` wires them together.

## Configuration and deploy

Every setting is an `APP_*` environment variable, listed in `.env.example`. In a
cluster the same names come from a ConfigMap and a Secret. The image is built from
the `Dockerfile` (multi-stage, non-root, one process).
