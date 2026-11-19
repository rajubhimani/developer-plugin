# Python in containers: Docker, Compose and Kubernetes

Most Python services end up in a container, run locally with Compose and in a
cluster with Kubernetes. This guide keeps those three the same app with different
configuration. Files to copy: `Dockerfile.python`, `compose.python.yaml`,
`env.example` and `dockerignore.python` in this folder. The cluster side is in the
`kubernetes` skill.

## The path of one setting

The same variable name is used everywhere; only where its value comes from changes.

| Where | Source of values | Notes |
|---|---|---|
| Code | `Settings` class with typed fields and defaults for non-secrets | One place that reads the environment |
| Local, no container | `.env` file (git-ignored) read by the settings class | Copy from `.env.example` |
| Compose | `.env` for the compose file's own `${VAR}` substitution, `env_file:` to pass values into the container | `docker compose config` prints the resolved result |
| Kubernetes | ConfigMap for plain values, Secret (synced from a secrets manager) for credentials | Real environment variables; no `.env` in the image |

Rules:
1. **The environment wins over the file.** The settings class reads real
   environment variables first and `.env` only as a local fallback, so a value set
   by the cluster always overrides a stray file.
2. **`.env` never goes into an image or git.** List it in `.gitignore` and
   `.dockerignore`. Commit `.env.example` with names and safe dummy values.
3. **No `if ENV == "production"` branches** in the settings code. Differences are
   values, not code paths.
4. **Fail at start-up** on a missing required setting, with its name in the message.
5. **Keep three lists in step:** the keys in `.env.example`, the fields in the
   `Settings` class and the keys in the Kubernetes ConfigMap and Secret.
   `make check-env` compares them and `make check` runs it (see `settings.py` in
   this folder for the template). Names are checked, not values: start-up
   validation rejects a bad value.
6. **Secrets as files are fine:** a mounted secret directory can be read by the
   settings class (`secrets_dir`) and kept out of the process environment.

## Dockerfile: layers and caching

A Docker image is a stack of layers. A layer is rebuilt when its instruction or
any input before it changes, and everything after it is rebuilt too. Order from
least to most often changing:

1. Base image and OS settings (rarely).
2. The package manager binary (rarely).
3. **Dependencies,** from `pyproject.toml` and `uv.lock` only (when the lock
   changes).
4. **Your source** (every commit).

So the dependency install must not see the source. Install with
`--no-install-project` first, copy the source, then install the project itself.
A source edit then rebuilds only the last small layer.

Cache layers:
- **Layer cache** reuses unchanged steps on the same builder.
- **BuildKit cache mounts** (`RUN --mount=type=cache,target=...`) keep the
  package download cache between builds, so a changed lock file re-downloads only
  what changed. The mount is not part of the image.
- **Bind mounts** for the lock and project files let the dependency step read
  them without a `COPY` layer.
- **In CI** the builder is often fresh. Export and import the cache from a
  registry or the CI cache backend (`--cache-to` and `--cache-from`); look up the
  options for your builder. Build stages that never reach the final image lose
  their layers, so the cache must be exported with all stages.

## Multi-stage

| Stage | Holds | Reaches the final image? |
|---|---|---|
| `base` | Python base, environment variables, workdir | Yes (parent of runtime) |
| `builder` | package manager, compilers if needed, the virtual environment | Only the environment is copied |
| `dev` (optional) | builder plus dev tools and auto-reload, for Compose | No |
| `test` (optional) | builder plus test tools, run in CI | No |
| `runtime` | base, a non-root user, the copied environment and code | Yes |

Rules:
- **Same base for build and run,** so the interpreter path and the platform
  match; a virtual environment holds absolute paths. Build it where it will run
  (the same directory in both stages).
- **Install the project non-editable** so the copied environment is self-contained
  and the final stage needs no source tree.
- **Prefer a slim Debian-based image.** Alpine uses a different C library, so many
  prebuilt wheels are missing and builds get slow and fragile. Consider a
  distroless Python base only when the team can debug without a shell.
- **Compilers live in the builder only.** If a package needs system libraries to
  build, install them there, and install only the runtime libraries in the final
  stage.
- **Pin the base by digest** for releases and update by review (see `docker`).

## Runtime settings that matter

- `PYTHONUNBUFFERED=1` so logs appear at once instead of when a buffer fills.
- `PYTHONDONTWRITEBYTECODE=1` in the image if the filesystem is read-only; compile
  bytecode at build time instead so start-up is fast.
- **Run as a non-root user** with a numeric id, and make writable paths explicit.
  A read-only root filesystem needs a temp directory mounted (see `kubernetes`).
- **Exec-form `CMD`** (`["uvicorn", ...]`), never shell form. The shell would be
  process 1, would not pass SIGTERM on, and the pod would be killed after the grace
  period instead of stopping cleanly. Compose's `init: true` can hide this, so test
  the stop time without it.
- **One server process per container on Kubernetes.** Scale with replicas and let
  the cluster restart and schedule them. Use a multi-process manager only when you
  have measured a need. Size worker counts to the CPU the container is given, not
  the host.
- **Handle SIGTERM:** finish in-flight requests, stop accepting new ones, then
  exit, within the termination grace period. Make readiness fail first.
- **Health endpoints:** a cheap liveness route (the process answers) and a
  readiness route (it can serve, dependencies reachable). Kubernetes ignores the
  image's `HEALTHCHECK`; use probes there. The slim image has no `curl`, so use the
  app's own command or a Python one-liner if you keep a `HEALTHCHECK` for Compose.
- **Log to standard output** as structured lines; the platform collects them.
- **Memory:** set a limit and watch real use; garbage collection and large
  imports can surprise. Do not assume the host's CPU count.

## Compose for local work

- Start everything with `docker compose up --build --wait`.
- The `dev` target runs with auto-reload and `develop.watch` syncs source and
  rebuilds when `pyproject.toml` or `uv.lock` change.
- Dependencies (database, cache, queue) have healthchecks and the app waits with
  `condition: service_healthy`. A migration runs as a one-shot service and the app
  waits for `service_completed_successfully`.
- Optional tools (admin UI, mail catcher) sit behind a profile.
- Bind ports to `127.0.0.1`. Use named volumes for data.
- Local database passwords in `.env` are dummies; never reuse real ones.
- Run the same image the cluster runs (the `runtime` target) in a CI smoke test
  with `docker compose --profile ... up --wait`, so what you test is what ships.

## Kubernetes hand-off

Build once, tag by commit, push, deploy the digest. Configuration comes from the
ConfigMap and Secret, not from the image. Details, manifests and the checklist are
in the `kubernetes` skill.

## Check before you ship

1. `docker build` twice: the second run is almost all cache hits. Change one
   source line: only the last layers rebuild.
2. `docker run --rm <image> id` shows a non-root user.
3. `docker stop` returns in a second or two, not ten (signals reach the app).
4. The image has no `.env`, no `.git`, no tests unless intended, no compilers.
5. `docker history` and an image scan show nothing secret and no known severe
   vulnerability.
6. `docker compose config` shows the values you expect.
