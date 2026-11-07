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
