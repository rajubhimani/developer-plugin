---
name: compose
description: "Docker Compose: healthchecks, dependency order, volumes, profiles, env files. Use for compose.yaml or running several containers together."
metadata:
  verified: "2026-11-07"
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

## Environment and `.env`

- **Two jobs, do not mix them up.** A `.env` file next to `compose.yaml` fills
  `${VAR}` inside the compose file. `env_file:` passes a file's values into a
  container. Use both on purpose and name the variables the same as the app's
  settings and the Kubernetes ConfigMap (see `kubernetes`).
- **Precedence:** command-line values and the shell beat `environment:`, which beats
  `env_file:`, which beats the image's own defaults. Run `docker compose config` to
  see the final values rather than guessing.
- `.env` is git-ignored and docker-ignored; `.env.example` is committed with names
  and dummy values only. Required values use `${VAR:?message}` so a missing one
  stops `up` with a clear message.
- Values that name another container (`db`) go under `environment:`; values that
  differ per developer go in `.env`.
- Run migrations as a one-shot service and wait with
  `condition: service_completed_successfully`.
- `init: true` runs a small init process and can hide a signal-handling bug that
  appears in a cluster. Also test the stop time without it, and use exec-form
  commands.
- Run the same image target that you ship in a CI smoke test with `up --wait`.
- A Python example stack (file `compose.python.yaml`) is in the `lang-python`
  skill's references folder.

## Checks

1. `docker compose config` must succeed.
2. `docker compose up --build --wait` must report all services healthy.
3. `docker compose down -v` to confirm a clean teardown in a throwaway run.

## Common mistakes

- Relying on `depends_on` alone, which only orders startup.
- Publishing database ports to all interfaces on a laptop.
- Committing `.env` with real credentials.

Use `templates/compose.yaml` as a starting point.
