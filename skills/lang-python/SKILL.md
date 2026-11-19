---
name: lang-python
description: Python project setup and quality gates (uv, src layout, ruff, pyright, pytest, lock files). Use when creating, changing, reviewing or running Python code or a Python package.
verified: 2026-11-07
---

# Python

## Current versions

Look these up when you start, never from memory:
- Python: the release feed `https://endoflife.date/api/python.json` (first entry).
- uv, ruff, pyright: `https://pypi.org/pypi/<name>/json`, field `info.version`.

## Setup

- Pin the interpreter in `.python-version` to the current stable release you looked up.
- Use `uv init --package` for a library or app, `uv add` for dependencies,
  `uv add --dev` for tools. Do not use `pip install` or `requirements.txt`.
- Commit `pyproject.toml` and `uv.lock`. Upgrade with `uv lock --upgrade`, then
  run the checks.
- Keep every tool setting in `pyproject.toml`. Avoid extra config files.

## Layout

- `src/<package>/` for code, `tests/` beside it. The src layout stops tests from
  importing the working copy instead of the installed package.
- One module, one job. Public functions have type hints and docstrings.

## Reuse before writing

- Check numpy, pandas, the standard library and the framework in use before
  writing a numeric, array or text helper. `np.mean`, `np.pad`,
  `torch.nn.utils.rnn.pad_sequence` and `collections.Counter` are tested and
  fast; a loop or a one-line `sum(x) / len(x)` is slower and untested.
- Reducing an empty collection (mean, max, argmax) is a bug. Check the length
  first and fail clearly. A library may return `nan` and a warning, which is
  better than a silent wrong value, but the check belongs in the caller.
- Keep your own version only with a stated reason in a comment, for example a
  library that calls a deprecated function when warnings are errors.

## Call by name

- Pass arguments to your own functions and classes by keyword, one per line
  when the call is long:
  ```python
  Token(
      id=int(cols[0]),
      form=cols[1],
      head=int(cols[6]),
  )
  ```
  A reader sees what each value is without opening the definition, and
  reordering or inserting a parameter cannot silently swap two values of the
  same type (`head` and `id` are both `int`).
- Exceptions: a call with one obvious argument (`len(xs)`, `Path(p)`), and
  library functions that only accept positional arguments (many builtins and
  numpy functions), callbacks typed `Callable[[A, B], R]`, which have no
  parameter names, and the `*args` part of a variadic call. Do not rewrite
  those.
- When changing existing code, match calls to definitions by what they resolve
  to, not by name: `pad`, `encode` and `load` also exist in libraries. Run the
  type checker afterwards, since a wrong keyword fails there.
- In a definition, put `*` before parameters that callers should always name.
  A call that leaves one out then fails at once instead of working by accident.
- ruff has no rule for keyword calls in general (`FBT` covers booleans only),
  so check this in review.

## Fixed sets of values

- Use a `StrEnum` for any fixed set of string values (statuses, modes, kinds).
  Do not write a `Literal[...]` type and a tuple of the same words: the two
  drift apart. Derive any list from the enum (`tuple(Status)`), never retype it.
- A `StrEnum` member is still a string. It equals plain text, and `json.dumps`
  and CSV write it as plain text, so saved files do not change.
- A member's default `repr` is noisy (`<Status.OPEN: 'open'>`) in logs and
  dataclass reprs. Give the project one small base class with
  `__repr__ = str.__repr__` and subclass it, so these print `'open'`.
- Test membership with `value in Status` (a plain string works on current
  Python; older releases raised an error). Join the values for an error message
  with `", ".join(Status)`, not the tuple's repr.
- Keep `Literal` where a library already validates the value, such as a
  settings field read from the environment. An enum adds nothing there.
- Data loaded from JSON holds plain strings, not members. Convert on load
  (`Status(text)`) so the annotation is true and a bad value fails at load
  time, not later.
- When you move a set of values into an enum, search for every old string
  literal (`== "open"`) and replace it. Equal strings hide a half-finished
  migration until someone renames a member.
- Derive a subset of an enum from it; do not retype members. If a member's
  position matters (an index, a stored number), say so in a comment, since
  reordering members then changes what the stored data means.
- Move the comment that described the old constant into the enum's docstring,
  or it is left describing nothing.
- Parameters typed `list[Status]` reject a `list[str]` and the reverse, because
  `list` is invariant. Take a `Sequence[Status]` when a caller may pass either.

## Containers, Compose and Kubernetes

Most Python services run in a container, locally under Compose and in a cluster
under Kubernetes. Keep these three the same app with different configuration.

- **One `Settings` class** (template: `references/settings.py`, built on
  pydantic-settings) reads typed values from the environment, with `.env` only
  as a local fallback. Credentials are `SecretStr`, a missing required value stops
  start-up with its name, and a mounted secrets directory is supported.
  `make check-env` fails when the fields, `.env.example` and the cluster config
  disagree. `.env` is git-ignored and docker-ignored; `.env.example` is
  the committed list of names. Compose passes `.env` in; Kubernetes supplies the
  same names from a ConfigMap and a Secret (see `kubernetes`, `secrets-and-config`).
- **Multi-stage Dockerfile with uv:** dependencies from `pyproject.toml` and
  `uv.lock` only, in their own cached layer (`--no-install-project`), then the
  source, then a non-editable install. BuildKit cache mounts keep downloads between
  builds. Run as a numeric non-root user with an exec-form `CMD`.
- **One server process per container;** scale with replicas. Handle SIGTERM, expose
  liveness and readiness routes, log to standard output.
- `make init-project` copies these into a new project (never over an existing file):
  `references/Dockerfile.python`, `references/compose.python.yaml`,
  `references/env.example`, `references/dockerignore.python` and
  `references/settings.py`, plus `scripts/check_env.py`. The full guide, the
  layer and cache rules and the pre-ship checks are in `references/containers.md`.
- Idioms for errors, async, typing, logging, testing and security:
  `references/idioms.md`.

## Quality gates (run all, in this order)

1. `uv run ruff format --check .` and `uv run ruff check .`
2. `uv run pyright` in strict mode (`[tool.pyright] typeCheckingMode = "strict"`).
3. `uv run pytest` with coverage if the project tracks it.
4. A dependency audit in CI (`pip-audit` or the equivalent your platform offers;
   confirm the current tool name in its docs).

## Common mistakes

- Mixing pip, poetry or conda with uv in one project.
- Editing `uv.lock` by hand.
- Turning type errors off globally instead of fixing or narrowing them.
- Tests that depend on the order they run in.

Source to check before relying on details: the uv, ruff, pyright and pytest
documentation.
