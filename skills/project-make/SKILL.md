---
name: project-make
description: "Standard make targets for every project (help, install, format, lint, test, check, build, run, docker-build, clean). Use when adding or changing a Makefile, or asked how to build, test or run a project."
verified: 2026-11-07
---

# Project make targets

Every project exposes the same target names. A developer or agent runs
`make help` first, then `make check` before reporting work done.

| Target | Meaning |
|---|---|
| `help` | List the targets with one-line descriptions. |
| `install` | Install dependencies from the lock file. |
| `format` | Rewrite files to the project style. |
| `lint` | Check style and static rules without changing files. |
| `test` | Run the test suite. |
| `align` | Check the project follows the plugin guidelines (`tests/alignment`). |
| `check` | `align`, `lint` and `test`: the gate before reporting work done. |
| `build` | Produce the release artifact. |
| `run` | Run the program or service locally. |
| `docker-build` | Build the container image, if the project has one. |
| `clean` | Remove build output and caches; never touch source or lock files. |

## Rules

- Targets call the language tool through the project's own lock file
  (for example `uv run`, `go`, `cargo`, `npm ci`), so `make` and CI run the same
  commands.
- Targets are `.PHONY` unless they name a real file.
- A target that cannot run on this machine says so and exits non-zero, rather
  than silently passing.
- Keep the Makefile short: put logic in scripts, and let targets call them.

`templates/makefiles/<language>.mk` contains a working starting point for each
supported language. `make init-project` copies it into a repo.
