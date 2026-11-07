---
name: compose
description: Docker Compose practice for local development and multi-service setups (Compose Specification files, healthchecks, dependency ordering, named volumes, profiles, watch mode, env files). Use when writing or changing compose.yaml or running several containers together.
verified: 2026-11-07
---

# Docker Compose

## Current tools

Look these up when you start: the Docker Compose release notes, and the Compose
Specification at the Compose documentation site. Use the file name `compose.yaml`.

## Principles

- **Use the Compose Specification.** Do not add a top-level `version:` key; the
  specification does not need it. Run `docker compose config` to validate.
- **Require explicit image tags.** For third-party services, read the tag from a
  variable and fail if it is missing, so nobody runs a floating tag by accident.
  `templates/compose.yaml` shows the pattern.
- **Wait for dependencies to be healthy,** not just started. Use a healthcheck on
  the dependency and `depends_on` with `condition: service_healthy`.
- **Named volumes for data,** bind mounts only for source code in development.
- **Secrets stay out of git.** Keep local values in `.env` (git-ignored) and commit
  a `.env.example` with the variable names and no values.
- **Profiles for optional services** (debug tools, admin UIs), so the default
  `up` starts only what the app needs.
- **Development loop:** use `develop` with `watch` rules to sync or rebuild on
  change, rather than mounting the whole tree and running as root.
- **Ports bound to localhost** unless another machine must reach them:
  `"127.0.0.1:<host>:<container>"`.

## Checks

1. `docker compose config` must succeed.
2. `docker compose up --build --wait` must report all services healthy.
3. `docker compose down -v` to confirm a clean teardown in a throwaway run.

## Common mistakes

- Relying on `depends_on` alone, which only orders startup.
- Publishing database ports to all interfaces on a laptop.
- Committing `.env` with real credentials.

Use `templates/compose.yaml` as a starting point.
